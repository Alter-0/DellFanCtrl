@echo off
echo === Dell Fan Controller Frontend Development ===
echo.

cd frontend

REM 检查 node_modules
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo.
echo Starting frontend on http://localhost:5173
echo.

call npm run dev
