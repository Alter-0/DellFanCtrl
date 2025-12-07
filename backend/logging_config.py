import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os

LOG_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "logs"))
LOG_FILE = LOG_DIR / "fan_controller.log"

def setup_logging(ws_manager=None):
    """配置日志系统"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 创建根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 文件处理器 - 带轮转
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    
    # WebSocket 处理器（可选）
    if ws_manager:
        ws_handler = WebSocketLogHandler(ws_manager)
        ws_handler.setLevel(logging.INFO)
        logger.addHandler(ws_handler)
    
    return logger

class WebSocketLogHandler(logging.Handler):
    """将日志推送到 WebSocket 客户端"""
    
    def __init__(self, ws_manager):
        super().__init__()
        self.ws_manager = ws_manager
    
    def emit(self, record):
        try:
            import asyncio
            message = {
                "type": "log",
                "data": {
                    "time": self.formatTime(record),
                    "level": record.levelname,
                    "message": record.getMessage()
                }
            }
            # 异步发送
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.ws_manager.broadcast(message))
            except RuntimeError:
                pass  # 没有运行中的事件循环
        except Exception:
            pass
    
    def formatTime(self, record):
        import time
        ct = time.localtime(record.created)
        return time.strftime("%Y-%m-%d %H:%M:%S", ct) + f",{int(record.msecs):03d}"
