@echo off
echo 🏛️ Starting NSW Government Procurement Automation Platform...
echo.
echo 📍 Project directory: %CD%
echo 🔧 Applying OMP conflict fix...
echo 🚀 Launching Streamlit app...
echo.

REM Set OMP environment variable to fix library conflict
set KMP_DUPLICATE_LIB_OK=TRUE

REM Start the Streamlit app
python -m streamlit run app/streamlit_app.py --server.port 8501

pause
