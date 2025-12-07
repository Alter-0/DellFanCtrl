@echo off
echo === Dell Fan Controller Development ===
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM 安装后端依赖
echo Installing backend dependencies...
.venv\Scripts\pip install -q -r backend\requirements.txt

REM 创建数据目录
if not exist "data\logs" mkdir data\logs

REM 启动后端
echo.
echo Starting backend on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

cd backend
..\\.venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
