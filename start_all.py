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

def run_command(command, cwd=None, background=False):
    """Run a command and return the process"""
    print(f"Running: {command}")
    try:
        if background:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return process
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, check=True)
            return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
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
    """Install npm deps for landing and frontend"""
    print("Installing JavaScript dependencies...")
    try:
        if not run_command("npm install", cwd="landing"):
            print("Failed to install landing dependencies")
            return False
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
        "Dockerfile",
        "pyproject.toml",
        "poetry.lock",
        "backend/setup_database.py",
        "backend/api/main.py",
        "frontend/package.json",
        "landing/package.json"
    ]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    print("All required files found")
    return True

def delete_database():
    """Delete existing database if it exists"""
    db_path = "backend/portfolio.db"
    try:
        if os.path.exists(db_path):
            print("Deleting existing database...")
            os.remove(db_path)
            print("Database deleted successfully")
        else:
            print("No existing database found")
        return True
    except Exception as e:
        print(f"Error deleting database: {e}")
        return False

def setup_database():
    """Setup database with sample data - with fallback to import"""
    print("Setting up database...")
    if run_command("cd backend && poetry run python setup_database.py"):
        print("Database setup completed successfully!")
        return True
    print("Standard database setup failed!")
    return False

def check_ports_available():
    """Check if required ports are available"""
    import socket
    ports_to_check = [3000, 3001, 8000]
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

def main():
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DOCKER START ALL")
    print("=" * 60)
    
    print("\nPerforming sanity checks...")
    if not check_required_files(): return
    if not check_poetry_installed(): return
    if not check_docker_installed(): return
    if not check_docker_running(): return
    if not check_docker_compose(): return
    if not check_ports_available(): return

    print("All sanity checks passed!")

    print("\nStep 0: Installing Python dependencies...")
    if not install_dependencies(): return

    print("\nStep 0b: Installing JavaScript dependencies...")
    if not install_js_dependencies(): return

    print("\nStep 1: Cleaning up existing database...")
    if not delete_database(): return

    print("\nStep 2: Setting up database...")
    if not setup_database(): return

    print("\nStep 3: Starting Docker services...")
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
    print("Frontend (Alt): http://localhost:3001")
    print("Backend: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop everything")
    print("=" * 60)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Docker services...")
        run_command("docker compose down")
        print("Docker services stopped. Cleanup completed.")
        print("Goodbye!")

if __name__ == "__main__":
    main()
