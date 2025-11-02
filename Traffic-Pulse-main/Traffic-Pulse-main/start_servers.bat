@echo off
echo Starting Traffic Pulse Ultimate System...

echo Starting FastAPI server...
start "API Server" cmd /k "python api_server.py"

timeout /t 3

echo Starting Ultimate Traffic Dashboard...
start "Traffic Dashboard" cmd /k "streamlit run ultimate_traffic_dashboard.py --server.port=8501"

echo.
echo Services started:
echo - API Server: http://localhost:8082
echo - Ultimate Dashboard: http://localhost:8501
echo - API Docs: http://localhost:8082/docs
echo.
pause