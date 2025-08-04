#!/usr/bin/env python3
"""
Script to run the IBKR backend API
"""

import uvicorn
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.main import app

if __name__ == "__main__":
    print("Starting IBKR Backend API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 