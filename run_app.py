#!/usr/bin/env python3
"""
Run the NSW Procurement Platform with modular structure
"""
import os
import sys
import subprocess

# Fix OMP library conflict
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

if __name__ == "__main__":
    try:
        # Run streamlit from project root with app/main.py
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app/main.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except Exception as e:
        print(f"Error running app: {e}")
        sys.exit(1)
