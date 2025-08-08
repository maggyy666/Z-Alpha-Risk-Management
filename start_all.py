#!/usr/bin/env python3
"""
Start everything with Docker: setup database, start containers
"""

import subprocess
import sys
import os
import time
import signal
import requests
import shutil

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
        # First, ensure poetry.lock is up to date
        if not run_command("poetry lock"):
            print("Failed to update poetry.lock")
            return False
        
        # Install dependencies
        if not run_command("poetry install"):
            print("Failed to install dependencies")
            return False
        
        print("Dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"Error installing dependencies: {e}")
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
    for i in range(90):  # Wait up to 90 seconds for backend
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("Backend is ready!")
                return True
        except requests.exceptions.ConnectionError:
            if i % 10 == 0:  # Print status every 10 seconds
                print(f"Waiting for backend... ({i+1}/90 seconds)")
                # Check if containers are still running
                if i > 20 and not check_docker_containers_running():
                    print("Docker containers stopped running")
                    return False
        except requests.exceptions.RequestException as e:
            if i % 15 == 0:  # Print errors every 15 seconds
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
        "frontend/package.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("All required files found")
    
    # Check for sample data file as backup option
    sample_file = "z_alpha_sample_database.json"
    if os.path.exists(sample_file):
        file_size = os.path.getsize(sample_file)
        file_size_mb = file_size / (1024 * 1024)
        print(f"Sample data file available: {sample_file} ({file_size_mb:.1f} MB)")
    else:
        print(f"Sample data file not found: {sample_file}")
        print("   If database setup fails, sample data will need to be generated")
    
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
    try:
        # First try the original setup (generates new data)
        if run_command("cd backend && poetry run python setup_database.py"):
            print("Database setup completed successfully!")
            return True
        else:
            print("Standard database setup failed!")
            print("Attempting to use pre-generated sample data as fallback...")
            
            # Check if sample data file exists
            sample_file = "z_alpha_sample_database.json"
            if os.path.exists(sample_file):
                print(f"Found sample data file: {sample_file}")
                print("Importing sample data...")
                
                # Copy sample file to backend directory for import script
                import shutil
                try:
                    shutil.copy(sample_file, "backend/z_alpha_sample_database.json")
                    print("Sample data file copied to backend directory")
                except Exception as e:
                    print(f"Warning: Could not copy sample file: {e}")
                
                if run_command("cd backend && poetry run python import_database.py"):
                    print("Sample data imported successfully!")
                    print("Database setup completed using pre-generated data!")
                    return True
                else:
                    print("Failed to import sample data!")
                    return False
            else:
                print(f"Sample data file not found: {sample_file}")
                print("Please ensure the sample data file exists or check your setup.")
                return False
                
    except Exception as e:
        print(f"Error setting up database: {e}")
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
    """Main function"""
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DOCKER START ALL")
    print("=" * 60)
    
    # Sanity checks
    print("\nPerforming sanity checks...")
    
    if not check_required_files():
        print("Sanity check failed: Missing required files")
        return
    
    if not check_poetry_installed():
        print("Sanity check failed: Poetry not installed")
        return
    
    if not check_docker_installed():
        print("Sanity check failed: Docker not installed")
        return
    
    if not check_docker_running():
        print("Sanity check failed: Docker not running")
        return
    
    if not check_docker_compose():
        print("Sanity check failed: Docker Compose not available")
        return
    
    if not check_ports_available():
        print("Sanity check failed: Ports not available")
        return
    
    print("All sanity checks passed!")
    
    # 0. Install dependencies
    print("\nStep 0: Installing Python dependencies...")
    if not install_dependencies():
        print("Failed to install dependencies")
        return
    
    # 1. Delete existing database
    print("\nStep 1: Cleaning up existing database...")
    if not delete_database():
        print("Failed to clean up database")
        return
    
    # 2. Setup database
    print("\nStep 2: Setting up database...")
    if not setup_database():
        return
    
    # 3. Start Docker services
    print("\nStep 3: Starting Docker services...")
    try:
        # Start Docker services in detached mode
        if not run_command("docker compose up --build --detach"):
            print("Failed to start Docker services")
            return
        
        print("Docker services started successfully")
        
        # Give Docker services time to initialize
        print("Waiting for Docker services to initialize...")
        time.sleep(5)
        
        # Wait for backend to be ready
        print("Waiting for backend to start...")
        if not check_backend_ready():
            print("Backend failed to start!")
            try:
                run_command("docker compose down")
            except Exception as e:
                print(f"Error stopping Docker services: {e}")
            return
        
        print("Backend is ready!")
        
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
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping Docker services...")
            
            # Stop Docker services
            try:
                run_command("docker compose down")
                print("Docker services stopped")
                print("Cleanup completed")
            except Exception as e:
                print(f"Error during cleanup: {e}")
            
            print("Goodbye!")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return

if __name__ == "__main__":
    main() 