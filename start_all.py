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

def check_backend_ready():
    """Check if backend is ready"""
    print("Checking if backend is ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("Backend is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        except Exception as e:
            print(f"Error checking backend: {e}")
        time.sleep(1)
    print("Backend failed to start within 30 seconds")
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
    """Setup database with sample data"""
    print("Setting up database...")
    try:
        if not run_command("cd backend && python setup_database.py"):
            print("Database setup failed!")
            return False
        print("Database setup completed successfully!")
        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

def check_ports_available():
    """Check if required ports are available"""
    import socket
    
    ports_to_check = [3000, 8000]
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
        docker_process = run_command(
            "docker compose up --build",
            background=True
        )
        
        if not docker_process:
            print("Failed to start Docker services")
            return
        
        # Wait for backend to be ready
        print("Waiting for backend to start...")
        if not check_backend_ready():
            print("Backend failed to start!")
            try:
                docker_process.terminate()
                run_command("docker compose down")
            except Exception as e:
                print(f"Error stopping Docker services: {e}")
            return
        
        print("Backend is ready!")
        
        print("\n" + "=" * 60)
        print("EVERYTHING IS RUNNING!")
        print("=" * 60)
        print("\nFrontend: http://localhost:3000")
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
                if docker_process:
                    docker_process.terminate()
                    print("Docker services stopped")
                
                # Clean up
                run_command("docker compose down")
                print("Cleanup completed")
            except Exception as e:
                print(f"Error during cleanup: {e}")
            
            print("Goodbye!")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return

if __name__ == "__main__":
    main() 