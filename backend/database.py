from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 确保数据目录存在
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'fan_controller.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

class FanCurve(Base):
    __tablename__ = "fan_curve"
    id = Column(Integer, primary_key=True, autoincrement=True)
    temperature = Column(Integer, nullable=False)
    fan_speed = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MonitorHistory(Base):
    __tablename__ = "monitor_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cpu_temp = Column(Float, nullable=False)
    fan_speed = Column(Integer, nullable=False)
    power_consumption = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 初始化默认配置
        if not db.query(Settings).first():
            defaults = [
                Settings(key="ip_address", value=""),
                Settings(key="username", value="root"),
                Settings(key="password", value=""),
                Settings(key="interval", value="30"),
            ]
            db.add_all(defaults)
            db.commit()
        
        # 初始化默认风扇曲线
        if not db.query(FanCurve).first():
            default_curve = [
                FanCurve(temperature=50, fan_speed=15),
                FanCurve(temperature=60, fan_speed=15),
                FanCurve(temperature=70, fan_speed=20),
                FanCurve(temperature=80, fan_speed=40),
            ]
            db.add_all(default_curve)
            db.commit()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
