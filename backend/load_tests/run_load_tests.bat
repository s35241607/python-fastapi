@echo off
REM Enterprise Load Testing Suite for Windows
REM Automated testing scenarios for 1000+ concurrent users

echo === Enterprise Ticket Management System Load Testing ===
echo Target: 1000+ concurrent users simulation
echo Date: %date% %time%
echo.

REM Configuration
set HOST=http://localhost:8000
set RESULTS_DIR=.\load_test_results
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM Create results directory
if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"

echo Setting up load test environment...

REM Check if Python and required packages are installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install requirements if needed
pip install -r requirements.txt >nul 2>&1

echo.
echo === Running Enterprise Normal Load Test ===
echo Description: Normal enterprise load - 500 concurrent users over 5 minutes
echo Users: 500, Spawn Rate: 10/s, Duration: 300s

locust -f locustfile.py --host="%HOST%" --users=500 --spawn-rate=10 --run-time=300s --headless --csv="%RESULTS_DIR%\enterprise_normal_%TIMESTAMP%" --html="%RESULTS_DIR%\enterprise_normal_%TIMESTAMP%.html" --loglevel=INFO --logfile="%RESULTS_DIR%\enterprise_normal_%TIMESTAMP%.log"

echo.
echo === Running Enterprise Peak Load Test ===
echo Description: Peak enterprise load - 1000 concurrent users over 10 minutes
echo Users: 1000, Spawn Rate: 20/s, Duration: 600s

locust -f locustfile.py --host="%HOST%" --users=1000 --spawn-rate=20 --run-time=600s --headless --csv="%RESULTS_DIR%\enterprise_peak_%TIMESTAMP%" --html="%RESULTS_DIR%\enterprise_peak_%TIMESTAMP%.html" --loglevel=INFO --logfile="%RESULTS_DIR%\enterprise_peak_%TIMESTAMP%.log"

echo.
echo === Running Enterprise Stress Test ===
echo Description: Stress testing - 1500 concurrent users to test breaking point
echo Users: 1500, Spawn Rate: 25/s, Duration: 300s

locust -f locustfile.py --host="%HOST%" --users=1500 --spawn-rate=25 --run-time=300s --headless --csv="%RESULTS_DIR%\enterprise_stress_%TIMESTAMP%" --html="%RESULTS_DIR%\enterprise_stress_%TIMESTAMP%.html" --loglevel=INFO --logfile="%RESULTS_DIR%\enterprise_stress_%TIMESTAMP%.log"

echo.
echo === Running Enterprise Spike Test ===
echo Description: Spike testing - 2000 users spawned rapidly
echo Users: 2000, Spawn Rate: 100/s, Duration: 180s

locust -f locustfile.py --host="%HOST%" --users=2000 --spawn-rate=100 --run-time=180s --headless --csv="%RESULTS_DIR%\enterprise_spike_%TIMESTAMP%" --html="%RESULTS_DIR%\enterprise_spike_%TIMESTAMP%.html" --loglevel=INFO --logfile="%RESULTS_DIR%\enterprise_spike_%TIMESTAMP%.log"

echo.
echo === Running Enterprise Endurance Test ===
echo Description: Endurance testing - 800 users for 30 minutes sustained load
echo Users: 800, Spawn Rate: 10/s, Duration: 1800s

locust -f locustfile.py --host="%HOST%" --users=800 --spawn-rate=10 --run-time=1800s --headless --csv="%RESULTS_DIR%\enterprise_endurance_%TIMESTAMP%" --html="%RESULTS_DIR%\enterprise_endurance_%TIMESTAMP%.html" --loglevel=INFO --logfile="%RESULTS_DIR%\enterprise_endurance_%TIMESTAMP%.log"

echo.
echo === Load Testing Complete ===
echo All results saved to: %RESULTS_DIR%
echo.

REM Generate summary report
python generate_report.py "%RESULTS_DIR%" "%TIMESTAMP%"

echo.
echo Load testing suite completed successfully!
echo Check the HTML reports for detailed performance analysis.
echo.
pause