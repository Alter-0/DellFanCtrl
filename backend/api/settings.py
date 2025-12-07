from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db, Settings

router = APIRouter()

# 全局引用，将在 main.py 中设置
monitor_service = None

def set_monitor_service(service):
    global monitor_service
    monitor_service = service

class SettingsResponse(BaseModel):
    ip_address: str
    username: str
    password: str
    interval: int

class SettingsUpdateRequest(BaseModel):
    ip_address: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    interval: Optional[int] = None

@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """获取系统设置"""
    settings = {s.key: s.value for s in db.query(Settings).all()}
    return SettingsResponse(
        ip_address=settings.get("ip_address", ""),
        username=settings.get("username", ""),
        password="******" if settings.get("password") else "",
        interval=int(settings.get("interval", 30))
    )

@router.put("")
async def update_settings(request: SettingsUpdateRequest, db: Session = Depends(get_db)):
    """更新系统设置"""
    updates = request.model_dump(exclude_none=True)
    
    # 验证间隔时间
    if "interval" in updates and not (5 <= updates["interval"] <= 300):
        raise HTTPException(status_code=400, detail="间隔时间必须在5-300秒之间")
    
    for key, value in updates.items():
        setting = db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            db.add(Settings(key=key, value=str(value)))
    
    db.commit()
    
    # 通知监控服务重新加载配置
    if monitor_service:
        await monitor_service.reload_settings()
    
    return {"success": True}
