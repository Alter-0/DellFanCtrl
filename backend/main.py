from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os

from api import dashboard, curve, logs, settings
from services.monitor_service import MonitorService
from services.websocket_service import WebSocketManager
from services.cleanup_service import DataCleanupService
from database import init_db, SessionLocal, Settings
from logging_config import setup_logging
from version import __version__

ws_manager = WebSocketManager()
monitor_service = MonitorService(ws_manager)
cleanup_service: DataCleanupService = None

# 设置 API 模块的监控服务引用
dashboard.set_monitor_service(monitor_service)
settings.set_monitor_service(monitor_service)
curve.set_monitor_service(monitor_service)

def get_retention_days_from_db() -> int:
    """从数据库获取保留天数配置"""
    db = SessionLocal()
    try:
        setting = db.query(Settings).filter(Settings.key == "retention_days").first()
        return int(setting.value) if setting else DataCleanupService.DEFAULT_RETENTION_DAYS
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cleanup_service
    
    # 启动时初始化
    setup_logging(ws_manager)
    init_db()
    
    # 初始化数据清理服务，从数据库读取保留期限配置
    retention_days = get_retention_days_from_db()
    cleanup_service = DataCleanupService(retention_days=retention_days)
    
    # 设置 settings API 的清理服务引用
    settings.set_cleanup_service(cleanup_service)
    
    # 启动服务
    asyncio.create_task(monitor_service.start())
    await cleanup_service.start()
    
    yield
    
    # 关闭时清理
    await monitor_service.stop()
    await cleanup_service.stop()

app = FastAPI(
    title="Dell Fan Controller",
    version=__version__,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(curve.router, prefix="/api/curve", tags=["Curve"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])

@app.get("/api/version", tags=["System"])
async def get_version():
    """获取系统版本信息"""
    return {"version": __version__}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# 挂载静态文件（如果存在）
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
