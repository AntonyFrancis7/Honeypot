@echo off
echo Starting Flask Backend on port 5000...
cd backend
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
start "Honeypot Backend" python app.py
cd ..

echo Starting React Frontend...
cd honeypot-collegeportal
call npm install
start "Honeypot Frontend" npm run dev
cd ..

echo Both services started in separate windows.
