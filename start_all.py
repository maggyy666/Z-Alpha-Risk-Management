#!/usr/bin/env python3
"""
Start everything with Docker: setup database, start containers
"""

import subprocess
import sys
import os
import time
import signal
import shutil
import datetime
from pathlib import Path


def load_env_file():
    """Load key=value pairs from .env or config.env.example into os.environ.
    Looks first for .env (real secrets), falls back to config.env.example only
    so that the script can explain to the user what is missing."""
    for candidate in (".env", "config.env"):
        path = Path(candidate)
        if not path.exists():
            continue
        print(f"Loading environment from {candidate}")
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().split("#", 1)[0].strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                # Do not overwrite a value already set in the real environment
                os.environ.setdefault(key, value)
        return True
    print("WARNING: no .env file found. Copy config.env.example to .env and edit.")
    return False


class _Tee:
    """Duplicate writes to the original stream AND a log file."""
    def __init__(self, original, log_file):
        self.original = original
        self.log_file = log_file

    def write(self, data):
        self.original.write(data)
        try:
            self.log_file.write(data)
            self.log_file.flush()
        except Exception:
            pass
        return len(data) if data is not None else 0

    def flush(self):
        try:
            self.original.flush()
        except Exception:
            pass
        try:
            self.log_file.flush()
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self.original, name)


def setup_logging():
    """Mirror stdout+stderr of this process (and its subprocess children via
    run_command streaming) into logs/run_YYYYMMDD_HHMMSS.log. Keeps only the
    last 20 run logs so the directory does not grow forever."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"run_{ts}.log"
    log_file = open(log_path, "w", encoding="utf-8", errors="replace", buffering=1)

    sys.stdout = _Tee(sys.stdout, log_file)
    sys.stderr = _Tee(sys.stderr, log_file)

    # Rotate: keep only the 20 most recent run_*.log files
    runs = sorted(logs_dir.glob("run_*.log"), key=lambda p: p.stat().st_mtime)
    for old in runs[:-20]:
        try:
            old.unlink()
        except Exception:
            pass

    print(f"=== Run started {ts} | log file: {log_path} ===")
    return log_file

# Import requests only when needed, using poetry environment
def get_requests():
    """Get requests module from poetry environment"""
    try:
        result = subprocess.run(
            ["cd backend && poetry run python -c 'import requests; print(\"OK\")'"],
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "requests", 
                subprocess.check_output(
                    ["cd backend && poetry run python -c 'import requests; print(requests.__file__)'"],
                    shell=True, text=True
                ).strip()
            )
            requests = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(requests)
            return requests
        else:
            import requests
            return requests
    except Exception:
        import requests 
        return requests

_WIN_SHELL_BUILTINS = {"cd", "echo", "set", "del", "dir", "copy", "type", "rem", "if", "for"}


def _resolve_first_token(command: str) -> str:
    """On Windows, resolve `npm`, `poetry`, etc. to an absolute path via
    shutil.which (which respects PATHEXT) so subprocess does not depend on
    how the parent shell expands command names."""
    if sys.platform != "win32":
        return command
    parts = command.split(None, 1)
    if not parts:
        return command
    head = parts[0]
    if head.lower() in _WIN_SHELL_BUILTINS:
        return command
    resolved = shutil.which(head)
    if not resolved:
        return command
    rest = parts[1] if len(parts) > 1 else ""
    quoted = f'"{resolved}"'
    return f"{quoted} {rest}" if rest else quoted


def run_command(command, cwd=None, background=False, env=None):
    """Run a command. In foreground, subprocess stdout/stderr is streamed line-by-line
    through print() so it flows into the Tee (terminal + log file).

    Forces UTF-8 for the child process so that emoji/non-ASCII prints don't crash
    on Windows (default cp1250). Resolves the executable via shutil.which on
    Windows because cmd.exe can fail to locate .cmd scripts depending on how
    the parent shell was launched (Git Bash, VS Code terminal, IDE, ...)."""
    command = _resolve_first_token(command)
    print(f"Running: {command}")
    # Force UTF-8 stdout/stderr in the child (fixes Windows cp1250 charmap errors)
    utf8_env = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    if env:
        merged_env = {**os.environ, **utf8_env, **env}
    else:
        merged_env = {**os.environ, **utf8_env}
    try:
        if background:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=merged_env,
            )
            return process

        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=merged_env,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
        process.wait()
        if process.returncode != 0:
            print(f"Command failed with exit code {process.returncode}")
            return False
        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def host_database_url():
    """DATABASE_URL for scripts running on the host (Postgres exposed on localhost:5432)."""
    user = os.environ.get("POSTGRES_USER", "zalpha")
    password = os.environ.get("POSTGRES_PASSWORD", "zalpha")
    db = os.environ.get("POSTGRES_DB", "zalpha")
    return f"postgresql+psycopg2://{user}:{password}@localhost:5432/{db}"


def wait_for_postgres(timeout_s=60):
    """Poll docker-compose healthcheck until Postgres reports healthy."""
    print("Waiting for Postgres to become healthy...")
    for _ in range(timeout_s):
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Health.Status}}", "zalpha-postgres"],
                shell=True, capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and "healthy" in result.stdout:
                print("Postgres is healthy")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("Postgres did not become healthy in time")
    return False

def check_poetry_installed():
    """Check if Poetry is installed and accessible"""
    try:
        result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Poetry found: {result.stdout.strip()}")
            return True
        else:
            print("Poetry is not installed or not accessible")
            return False
    except FileNotFoundError:
        print("Poetry command not found. Please install Poetry first.")
        return False
    except Exception as e:
        print(f"Error checking Poetry: {e}")
        return False

def install_dependencies():
    """Install Python dependencies using Poetry"""
    print("Installing Python dependencies...")
    try:
        if not run_command("poetry lock"):
            print("Failed to update poetry.lock")
            return False
        if not run_command("poetry install"):
            print("Failed to install dependencies")
            return False
        print("Python dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False

def install_js_dependencies():
    """Install npm deps for frontend"""
    print("Installing JavaScript dependencies...")
    try:
        if not run_command("npm install", cwd="frontend"):
            print("Failed to install frontend dependencies")
            return False
        print("JavaScript dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"Error installing JS dependencies: {e}")
        return False

def check_docker_installed():
    """Check if Docker is installed and accessible"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Docker found: {result.stdout.strip()}")
            return True
        else:
            print("Docker is not installed or not accessible")
            return False
    except FileNotFoundError:
        print("Docker command not found. Please install Docker first.")
        return False
    except Exception as e:
        print(f"Error checking Docker: {e}")
        return False

def check_docker_running():
    """Check if Docker daemon is running"""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Docker daemon is running")
            return True
        else:
            print("Docker daemon is not running. Please start Docker Desktop.")
            return False
    except Exception as e:
        print(f"Error checking Docker daemon: {e}")
        return False

def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Docker Compose found: {result.stdout.strip()}")
            return True
        else:
            print("Docker Compose is not available")
            return False
    except Exception as e:
        print(f"Error checking Docker Compose: {e}")
        return False

def check_docker_containers_running():
    """Check if Docker containers are running"""
    try:
        result = subprocess.run(["docker", "compose", "ps", "-q"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("Docker containers are running")
            return True
        else:
            print("Docker containers are not running")
            return False
    except Exception as e:
        print(f"Error checking Docker containers: {e}")
        return False

def check_backend_ready():
    """Check if backend is ready"""
    print("Checking if backend is ready...")
    requests = get_requests()
    for i in range(90):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("Backend is ready!")
                return True
        except requests.exceptions.ConnectionError:
            if i % 10 == 0:
                print(f"Waiting for backend... ({i+1}/90 seconds)")
                if i > 20 and not check_docker_containers_running():
                    print("Docker containers stopped running")
                    return False
        except requests.exceptions.RequestException as e:
            if i % 15 == 0:
                print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error checking backend: {e}")
        time.sleep(1)
    print("Backend failed to start within 90 seconds")
    return False

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        "docker-compose.yml",
        "Dockerfile.backend",
        "Dockerfile.frontend",
        "pyproject.toml",
        "poetry.lock",
        "backend/setup_database.py",
        "backend/api/main.py",
        "frontend/package.json"
    ]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    print("All required files found")
    return True

def reset_postgres_volume():
    """Stop containers and drop the Postgres volume for a clean rebuild."""
    try:
        print("Stopping any running containers and dropping Postgres volume...")
        subprocess.run(["docker", "compose", "down", "-v"],
                       shell=True, capture_output=True, text=True, timeout=60)
        return True
    except Exception as e:
        print(f"Error resetting Postgres volume: {e}")
        return False

def setup_database():
    """Setup database with real market data from IBKR.
    Runs on host, so DATABASE_URL points to localhost (where Postgres is exposed)."""
    print("Setting up database with real market data from IBKR TWS...")
    env = {"DATABASE_URL": host_database_url()}
    if run_command("cd backend && poetry run python setup_database.py", env=env):
        print("Database setup completed successfully!")
        return True
    print("Database setup failed!")
    return False

def check_ports_available():
    """Check if required ports are available"""
    import socket
    ports_to_check = [3000, 8000]  # Removed 3001 - no longer needed
    unavailable_ports = []
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
        except OSError:
            unavailable_ports.append(port)
    if unavailable_ports:
        print(f"Ports {unavailable_ports} are already in use. Please free them up first.")
        return False
    print("All required ports are available")
    return True

def check_ibkr_connection():
    """Check TWS socket reachability without importing backend modules.
    TWS API handshake is heavier; a TCP open is enough to know the port is up."""
    import socket
    host = os.environ.get("IBKR_HOST", "127.0.0.1")
    port = int(os.environ.get("IBKR_PORT", "7496"))
    print(f"Checking IBKR TWS socket {host}:{port}...")
    try:
        with socket.create_connection((host, port), timeout=5):
            print("IBKR TWS socket is open")
            return True
    except (OSError, socket.timeout) as e:
        print(f"IBKR TWS socket unreachable: {e}")
        print("  Start TWS (live: 7496, paper: 7497), enable API, whitelist 127.0.0.1")
        return False

def main():
    setup_logging()
    load_env_file()

    required = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB",
                "ADMIN_PASSWORD", "USER_PASSWORD", "AUTH_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}")
        print("Copy config.env.example to .env and fill in values.")
        return

    print("=" * 60)
    print("Z-ALPHA SECURITIES - DOCKER START ALL")
    print("NEW CONFIGURATION: Frontend (3000) + Backend (8000)")
    print("Live-reload enabled for both services")
    print("=" * 60)
    
    print("\nPerforming sanity checks...")
    if not check_required_files(): return
    if not check_poetry_installed(): return
    if not check_docker_installed(): return
    if not check_docker_running(): return
    if not check_docker_compose(): return
    if not check_ports_available(): return

    print("All basic sanity checks passed!")

    print("\nStep 0: Installing Python dependencies...")
    if not install_dependencies(): return

    print("\nStep 0b: Installing JavaScript dependencies...")
    if not install_js_dependencies(): return

    if not check_ibkr_connection():
        print("\nIBKR TWS is not available — aborting.")
        print("  Start IBKR TWS (paper: 7497, live: 7496) with API enabled and retry.")
        return

    print("\nStep 1: Resetting Postgres volume for clean rebuild...")
    if not reset_postgres_volume(): return

    print("\nStep 2: Starting Postgres service...")
    if not run_command("docker compose up -d postgres"):
        print("Failed to start Postgres")
        return
    if not wait_for_postgres():
        return

    print("\nStep 3: Seeding database with real market data from IBKR...")
    if not setup_database(): return

    print("\nStep 4: Starting backend and frontend services...")
    if not run_command("docker compose up --build --detach"):
        print("Failed to start Docker services")
        return

    print("Docker services started successfully")
    time.sleep(5)

    print("Waiting for backend to start...")
    if not check_backend_ready():
        print("Backend failed to start!")
        run_command("docker compose down")
        return

    print("\n" + "=" * 60)
    print("EVERYTHING IS RUNNING!")
    print("=" * 60)
    print("\nFrontend: http://localhost:3000")
    print("Backend API: http://localhost:8000")
    print("\nTo stop all services: docker compose down")
    print("To view logs: docker compose logs -f")
    print("To view specific service logs: docker compose logs -f frontend")
    print("To view backend logs: docker compose logs -f backend")
    print("\nPress Ctrl+C to stop all services")

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down all services...")
        run_command("docker compose down")
        print("All services stopped. Goodbye!")

if __name__ == "__main__":
    main()
