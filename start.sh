#!/bin/bash
set -e

echo "=== Dell Fan Controller Starting ==="

# 创建必要目录
mkdir -p /app/data/logs

# 启动后端服务（同时提供静态文件）
echo "Starting Backend API..."
cd /app/backend
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
