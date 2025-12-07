from fastapi import APIRouter, Query
from typing import Optional
import re
from pathlib import Path
import os

router = APIRouter()

# 日志文件路径
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "logs")
LOG_FILE = Path(LOG_DIR) / "fan_controller.log"

@router.get("")
def get_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取日志"""
    if not LOG_FILE.exists():
        return {"logs": []}
    
    logs = []
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.+)")
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in reversed(lines):
        match = pattern.match(line.strip())
        if not match:
            continue
        
        time_str, log_level, message = match.groups()
        
        # 级别过滤
        if level and log_level != level.upper():
            continue
        
        # 关键词搜索
        if search and search.lower() not in message.lower():
            continue
        
        logs.append({
            "time": time_str,
            "level": log_level,
            "message": message
        })
        
        if len(logs) >= limit:
            break
    
    return {"logs": logs}
