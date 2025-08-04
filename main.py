#!/usr/bin/env python3
"""
Simple FastAPI app runner
"""

import uvicorn
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from api.main import app
    print("✅ Successfully imported app")
    
    if __name__ == "__main__":
        print("Starting IBKR Backend API...")
        # Use import string for reload to work - note the backend. prefix
        uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["backend"])
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Current sys.path:", sys.path)
except Exception as e:
    print(f"❌ Error: {e}") 