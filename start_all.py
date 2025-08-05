#!/usr/bin/env python3
"""
Start everything: setup database, backend, and frontend
"""

import subprocess
import sys
import os
import time
import signal
import requests

def run_command(command, cwd=None, background=False):
    """Run a command and return the process"""
    print(f"🚀 Running: {command}")
    
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
        result = subprocess.run(command, shell=True, cwd=cwd)
        return result.returncode == 0

def check_backend_ready():
    """Check if backend is ready"""
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 Z-ALPHA SECURITIES - START ALL")
    print("=" * 60)
    
    # 1. Setup database
    print("\n📊 Step 1: Setting up database...")
    if not run_command("cd backend && poetry run python setup_database.py"):
        print("❌ Database setup failed!")
        return
    
    # 2. Start backend
    print("\n🔧 Step 2: Starting backend...")
    backend_process = run_command(
        "poetry run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000",
        cwd="backend",
        background=True
    )
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend to start...")
    if not check_backend_ready():
        print("❌ Backend failed to start!")
        backend_process.terminate()
        return
    
    print("✅ Backend is ready!")
    
    # 3. Start frontend
    print("\n🎨 Step 3: Starting frontend...")
    frontend_process = run_command(
        "npm start",
        cwd="frontend",
        background=True
    )
    
    print("\n" + "=" * 60)
    print("✅ EVERYTHING IS RUNNING!")
    print("=" * 60)
    print("\n🌐 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n🛑 Press Ctrl+C to stop everything")
    print("=" * 60)
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        
        # Stop frontend
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend stopped")
        
        # Stop backend
        if backend_process:
            backend_process.terminate()
            print("✅ Backend stopped")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main() 