from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db, FanCurve

router = APIRouter()

class CurvePoint(BaseModel):
    temp: int
    speed: int

class CurveResponse(BaseModel):
    points: List[CurvePoint]

class CurveUpdateRequest(BaseModel):
    points: List[CurvePoint]

@router.get("", response_model=CurveResponse)
def get_curve(db: Session = Depends(get_db)):
    """获取风扇曲线配置"""
    points = db.query(FanCurve).order_by(FanCurve.temperature).all()
    return CurveResponse(
        points=[CurvePoint(temp=p.temperature, speed=p.fan_speed) for p in points]
    )

@router.put("")
def update_curve(request: CurveUpdateRequest, db: Session = Depends(get_db)):
    """更新风扇曲线配置"""
    # 验证数据
    if len(request.points) < 2:
        raise HTTPException(status_code=400, detail="至少需要2个控制点")
    
    for point in request.points:
        if not (0 <= point.temp <= 100):
            raise HTTPException(status_code=400, detail=f"温度值无效: {point.temp}")
        if not (0 <= point.speed <= 100):
            raise HTTPException(status_code=400, detail=f"转速值无效: {point.speed}")
    
    # 清除旧数据
    db.query(FanCurve).delete()
    
    # 插入新数据
    for point in request.points:
        db.add(FanCurve(temperature=point.temp, fan_speed=point.speed))
    
    db.commit()
    return {"success": True}
