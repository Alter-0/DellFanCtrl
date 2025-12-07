from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db, MonitorHistory

router = APIRouter()

# 全局引用，将在 main.py 中设置
monitor_service = None

def set_monitor_service(service):
    global monitor_service
    monitor_service = service

@router.get("/status")
def get_status():
    """获取当前状态（从监控服务获取）"""
    if monitor_service is None:
        return {
            "cpu_temp": 0,
            "fan_speed": 0,
            "power": 0,
            "control_mode": "auto",
            "last_update": None
        }
    return dict(monitor_service.current_status)

@router.get("/history")
def get_history(range: str = "1h", db: Session = Depends(get_db)):
    """获取历史数据"""
    time_ranges = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
    }
    
    delta = time_ranges.get(range, timedelta(hours=1))
    since = datetime.utcnow() - delta
    
    records = db.query(MonitorHistory)\
        .filter(MonitorHistory.recorded_at >= since)\
        .order_by(MonitorHistory.recorded_at)\
        .all()
    
    return {
        "data": [
            {
                "time": r.recorded_at.isoformat(),
                "cpu_temp": r.cpu_temp,
                "fan_speed": r.fan_speed,
                "power": r.power_consumption
            }
            for r in records
        ]
    }

@router.post("/restore-auto")
async def restore_auto_control():
    """恢复自动风扇控制"""
    if monitor_service is None:
        raise HTTPException(status_code=500, detail="监控服务未启动")
    
    await monitor_service.restore_auto_control()
    return {"success": True}
