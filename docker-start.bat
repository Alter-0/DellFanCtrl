@echo off
echo === Dell Fan Controller Docker Deployment ===
echo.

set DOCKER_BUILDKIT=0
set COMPOSE_DOCKER_CLI_BUILD=0

echo [1/3] Building Docker image...
docker-compose build

echo.
echo [2/3] Starting container...
docker-compose up -d

echo.
echo [3/3] Checking status...
timeout /t 3 /nobreak >nul
docker-compose ps

echo.
echo ========================================
echo   Dell Fan Controller is running!
echo   Access: http://localhost:5936
echo ========================================
echo.
echo Press any key to view logs (Ctrl+C to exit)...
pause >nul
docker-compose logs -f
