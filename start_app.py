#!/usr/bin/env python3
"""
NSW Government Procurement Automation Platform
Startup script with OMP conflict fix
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Fix OMP library conflict
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    
    # Set working directory to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🏛️ Starting NSW Government Procurement Automation Platform...")
    print("📍 Project directory:", project_root)
    print("🔧 OMP conflict fix applied")
    print("🚀 Launching Streamlit app...")
    print()
    
    try:
        # Start Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/streamlit_app.py",
            "--server.port", "8501",
            "--server.headless", "true"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
