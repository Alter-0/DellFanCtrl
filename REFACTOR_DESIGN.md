# Dell 服务器风扇控制系统 - 重构设计文档

## 一、现有系统分析

### 1.1 当前架构问题

| 问题类型 | 具体问题 | 影响 |
|---------|---------|------|
| 架构耦合 | 风扇控制和日志展示是两个独立进程，无法实时通信 | 无法实时展示状态 |
| 前端简陋 | web_logger.py 仅用 HTML 字符串拼接，10秒刷新整页 | 用户体验差 |
| 配置管理 | 只能手动编辑 JSON 文件，需要重启生效 | 运维不便 |
| 数据存储 | 无历史数据存储，只有日志文件 | 无法分析趋势 |
| 风扇曲线 | 硬编码在配置文件，无可视化编辑 | 调整困难 |

### 1.2 现有功能清单

- ✅ IPMI 风扇控制（接管/恢复自动控制）
- ✅ 温度-转速线性插值计算
- ✅ 配置热重载（5分钟间隔）
- ✅ 错误重试机制
- ✅ 优雅退出（恢复自动控制）
- ✅ 基础日志展示

---

## 二、重构目标

### 2.1 功能需求

1. **可视化风扇曲线编辑器**
   - X轴：温度 (0-100°C)
   - Y轴：风扇转速 (0-100%)
   - 支持拖拽调整控制点
   - 支持添加/删除控制点
   - 实时预览曲线效果

2. **实时监控仪表盘**
   - 当前 CPU 温度显示
   - 当前风扇转速显示
   - 系统功耗显示
   - 数据每 5 秒自动刷新

3. **历史数据图表**
   - 温度/转速/功耗趋势图
   - 支持时间范围选择（1小时/6小时/24小时/7天）

4. **日志查看器**
   - 实时日志流
   - 日志级别过滤
   - 搜索功能


5. **系统配置管理**
   - iDRAC 连接配置
   - 监控间隔设置
   - 配置导入/导出

### 2.2 非功能需求

- 一键 Docker 部署
- 响应式 Web 界面
- 低资源占用
- 数据持久化

---

## 三、技术架构

### 3.1 技术栈选型

| 层级 | 技术 | 理由 |
|-----|------|------|
| 前端框架 | Vue 3 + Vite | 轻量、响应式、生态成熟 |
| UI 组件 | Element Plus | 企业级组件库，开箱即用 |
| 图表库 | ECharts | 功能强大，支持拖拽交互 |
| 后端框架 | FastAPI | 异步高性能，自动 API 文档 |
| 数据库 | SQLite | 轻量级，无需额外服务 |
| 实时通信 | WebSocket | 低延迟双向通信 |
| 容器化 | Docker + docker-compose | 一键部署 |

### 3.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Container                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Nginx (端口 80)                          ││
│  │         静态文件服务 + API 反向代理                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                   │
│  ┌─────────────────────┐       ┌─────────────────────────────┐  │
│  │   Vue 3 前端        │       │   FastAPI 后端 (端口 8000)   │  │
│  │   - 仪表盘          │◄─────►│   - REST API               │  │
│  │   - 曲线编辑器      │  WS   │   - WebSocket              │  │
│  │   - 日志查看器      │       │   - 风扇控制服务            │  │
│  │   - 系统设置        │       │   - 数据采集服务            │  │
│  └─────────────────────┘       └──────────────┬──────────────┘  │
│                                               │                  │
│                                               ▼                  │
│                                ┌─────────────────────────────┐  │
│                                │   SQLite 数据库              │  │
│                                │   - 历史数据                 │  │
│                                │   - 配置存储                 │  │
│                                └─────────────────────────────┘  │
│                                               │                  │
└───────────────────────────────────────────────┼──────────────────┘
                                                │
                                                ▼ IPMI/RACADM
                                    ┌─────────────────────┐
                                    │   Dell iDRAC        │
                                    │   服务器管理接口     │
                                    └─────────────────────┘
```

### 3.3 目录结构

```
dell-fan-controller/
├── docker-compose.yml          # Docker 编排文件
├── Dockerfile                  # 多阶段构建镜像
├── nginx.conf                  # Nginx 配置
│
├── backend/                    # 后端代码
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库模型
│   ├── fan_controller.py       # 风扇控制核心逻辑
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dashboard.py        # 仪表盘 API
│   │   ├── curve.py            # 曲线配置 API
│   │   ├── logs.py             # 日志 API
│   │   └── settings.py         # 设置 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ipmi_service.py     # IPMI 通信服务
│   │   ├── monitor_service.py  # 监控数据采集
│   │   └── websocket_service.py# WebSocket 管理
│   └── requirements.txt
│
├── frontend/                   # 前端代码
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/                # API 封装
│       │   └── index.js
│       ├── components/         # 组件
│       │   ├── Dashboard.vue   # 仪表盘
│       │   ├── CurveEditor.vue # 曲线编辑器
│       │   ├── LogViewer.vue   # 日志查看器
│       │   └── Settings.vue    # 系统设置
│       ├── stores/             # Pinia 状态管理
│       │   └── fan.js
│       └── styles/
│           └── main.css
│
└── data/                       # 持久化数据（挂载卷）
    ├── fan_controller.db       # SQLite 数据库
    └── logs/                   # 日志文件
```


---

## 四、数据库设计

### 4.1 表结构

```sql
-- 系统配置表
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 风扇曲线配置表
CREATE TABLE fan_curve (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature INTEGER NOT NULL,      -- 温度点 (°C)
    fan_speed INTEGER NOT NULL,        -- 风扇转速 (%)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 历史监控数据表
CREATE TABLE monitor_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpu_temp REAL NOT NULL,            -- CPU 温度
    fan_speed INTEGER NOT NULL,        -- 风扇转速
    power_consumption INTEGER,         -- 功耗 (W)
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为查询优化创建索引
CREATE INDEX idx_monitor_history_time ON monitor_history(recorded_at);
```

### 4.2 数据保留策略

| 时间范围 | 数据精度 | 保留时长 |
|---------|---------|---------|
| 实时 | 每次采集 | 24小时 |
| 历史 | 5分钟聚合 | 30天 |

---

## 五、API 设计

### 5.1 RESTful API

#### 仪表盘

```
GET /api/dashboard/status
响应: {
    "cpu_temp": 45.5,
    "fan_speed": 20,
    "power": 180,
    "control_mode": "manual",  // manual | auto
    "last_update": "2024-01-01T12:00:00Z"
}
```

#### 风扇曲线

```
GET /api/curve
响应: {
    "points": [
        {"temp": 50, "speed": 15},
        {"temp": 60, "speed": 15},
        {"temp": 70, "speed": 15},
        {"temp": 80, "speed": 40}
    ]
}

PUT /api/curve
请求: {
    "points": [
        {"temp": 50, "speed": 15},
        {"temp": 65, "speed": 20},
        {"temp": 80, "speed": 50}
    ]
}
响应: { "success": true }
```

#### 历史数据

```
GET /api/history?range=1h|6h|24h|7d
响应: {
    "data": [
        {
            "time": "2024-01-01T12:00:00Z",
            "cpu_temp": 45.5,
            "fan_speed": 20,
            "power": 180
        },
        ...
    ]
}
```

#### 日志

```
GET /api/logs?level=INFO|WARNING|ERROR&limit=100&search=keyword
响应: {
    "logs": [
        {
            "time": "2024-01-01T12:00:00",
            "level": "INFO",
            "message": "状态监测 - CPU: 45.5°C | 风扇: 20%"
        },
        ...
    ]
}
```

#### 系统设置

```
GET /api/settings
响应: {
    "ip_address": "192.168.2.111",
    "username": "root",
    "password": "******",
    "interval": 30
}

PUT /api/settings
请求: {
    "ip_address": "192.168.2.111",
    "username": "root",
    "password": "newpassword",
    "interval": 30
}
响应: { "success": true }
```

### 5.2 WebSocket API

```
连接: ws://host/ws

服务端推送消息格式:
{
    "type": "status_update",
    "data": {
        "cpu_temp": 45.5,
        "fan_speed": 20,
        "power": 180,
        "timestamp": "2024-01-01T12:00:00Z"
    }
}

{
    "type": "log",
    "data": {
        "level": "INFO",
        "message": "状态监测 - CPU: 45.5°C",
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```


---

## 六、核心代码实现

### 6.1 后端 - main.py

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from api import dashboard, curve, logs, settings
from services.monitor_service import MonitorService
from services.websocket_service import WebSocketManager
from database import init_db

ws_manager = WebSocketManager()
monitor_service = MonitorService(ws_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    init_db()
    asyncio.create_task(monitor_service.start())
    yield
    # 关闭时清理
    await monitor_service.stop()

app = FastAPI(title="Dell Fan Controller", lifespan=lifespan)

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

### 6.2 后端 - services/ipmi_service.py

```python
import asyncio
import subprocess
import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HardwareStatus:
    cpu_temp: float
    power: int

class IPMIService:
    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.username = username
        self.password = password
        self._manual_control = False
    
    async def _run_command(self, command: list, max_retries: int = 3) -> str:
        """异步执行命令，带重试机制"""
        for attempt in range(max_retries):
            try:
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
                
                if proc.returncode == 0:
                    return stdout.decode()
                
                logger.warning(f"命令执行失败 (尝试 {attempt + 1}/{max_retries}): {stderr.decode()}")
            except asyncio.TimeoutError:
                logger.warning(f"命令超时 (尝试 {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        raise RuntimeError(f"命令执行失败: {' '.join(command)}")
    
    async def get_hardware_status(self) -> HardwareStatus:
        """获取硬件状态"""
        data = await self._run_command([
            'racadm', '-r', self.ip, '-u', self.username, '-p', self.password,
            'getsensorinfo'
        ])
        
        cpu_temps = [int(m.group(1)) for m in re.finditer(r"CPU\d Temp\s+Ok\s+(\d+)C", data)]
        if not cpu_temps:
            raise ValueError("未找到有效的CPU温度数据")
        
        power_match = re.search(r"System Board Pwr Consumption\s+Ok\s+(\d+)Watts", data)
        
        return HardwareStatus(
            cpu_temp=sum(cpu_temps) / len(cpu_temps),
            power=int(power_match.group(1)) if power_match else 0
        )
    
    async def enable_manual_control(self) -> bool:
        """启用手动风扇控制"""
        try:
            await self._run_command([
                'ipmitool', '-I', 'lanplus', '-H', self.ip,
                '-U', self.username, '-P', self.password,
                'raw', '0x30', '0x30', '0x01', '0x00'
            ])
            self._manual_control = True
            logger.info("已启用手动风扇控制")
            return True
        except Exception as e:
            logger.error(f"启用手动控制失败: {e}")
            return False
    
    async def disable_manual_control(self) -> bool:
        """恢复自动风扇控制"""
        try:
            await self._run_command([
                'ipmitool', '-I', 'lanplus', '-H', self.ip,
                '-U', self.username, '-P', self.password,
                'raw', '0x30', '0x30', '0x01', '0x01'
            ])
            self._manual_control = False
            logger.info("已恢复自动风扇控制")
            return True
        except Exception as e:
            logger.error(f"恢复自动控制失败: {e}")
            return False
    
    async def set_fan_speed(self, percentage: int) -> bool:
        """设置风扇转速"""
        if not 0 <= percentage <= 100:
            raise ValueError(f"无效的风扇速度: {percentage}%")
        
        hex_speed = f"0x{percentage:02x}"
        try:
            await self._run_command([
                'ipmitool', '-I', 'lanplus', '-H', self.ip,
                '-U', self.username, '-P', self.password,
                'raw', '0x30', '0x30', '0x02', '0xff', hex_speed
            ])
            return True
        except Exception as e:
            logger.error(f"设置风扇转速失败: {e}")
            return False
    
    @property
    def is_manual_control(self) -> bool:
        return self._manual_control
```


### 6.3 后端 - services/monitor_service.py

```python
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple

from services.ipmi_service import IPMIService
from services.websocket_service import WebSocketManager
from database import get_db, MonitorHistory, FanCurve, Settings

logger = logging.getLogger(__name__)

class MonitorService:
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.ipmi: IPMIService = None
        self.running = False
        self.current_status = {
            "cpu_temp": 0,
            "fan_speed": 0,
            "power": 0,
            "control_mode": "auto"
        }
    
    def calculate_fan_speed(self, temp: float, curve: List[Tuple[int, int]]) -> int:
        """根据温度曲线计算风扇转速"""
        if not curve:
            return 20  # 默认安全转速
        
        curve = sorted(curve, key=lambda x: x[0])
        
        if temp <= curve[0][0]:
            return curve[0][1]
        if temp >= curve[-1][0]:
            return curve[-1][1]
        
        for i in range(len(curve) - 1):
            t0, s0 = curve[i]
            t1, s1 = curve[i + 1]
            if t0 <= temp < t1:
                # 线性插值
                return int(s0 + (temp - t0) * (s1 - s0) / (t1 - t0))
        
        return curve[-1][1]
    
    async def _load_settings(self):
        """从数据库加载配置"""
        db = next(get_db())
        settings = {s.key: s.value for s in db.query(Settings).all()}
        
        self.ipmi = IPMIService(
            ip=settings.get('ip_address', ''),
            username=settings.get('username', ''),
            password=settings.get('password', '')
        )
        self.interval = int(settings.get('interval', 30))
    
    async def _get_fan_curve(self) -> List[Tuple[int, int]]:
        """获取风扇曲线配置"""
        db = next(get_db())
        points = db.query(FanCurve).order_by(FanCurve.temperature).all()
        return [(p.temperature, p.fan_speed) for p in points]
    
    async def start(self):
        """启动监控服务"""
        self.running = True
        await self._load_settings()
        
        if not self.ipmi.ip:
            logger.error("未配置 iDRAC 地址，监控服务未启动")
            return
        
        # 接管风扇控制
        if await self.ipmi.enable_manual_control():
            self.current_status["control_mode"] = "manual"
        
        logger.info(f"监控服务已启动，间隔: {self.interval}秒")
        
        consecutive_errors = 0
        while self.running:
            try:
                # 获取硬件状态
                hw_status = await self.ipmi.get_hardware_status()
                
                # 获取风扇曲线并计算转速
                curve = await self._get_fan_curve()
                target_speed = self.calculate_fan_speed(hw_status.cpu_temp, curve)
                
                # 设置风扇转速
                await self.ipmi.set_fan_speed(target_speed)
                
                # 更新当前状态
                self.current_status.update({
                    "cpu_temp": hw_status.cpu_temp,
                    "fan_speed": target_speed,
                    "power": hw_status.power,
                    "last_update": datetime.now().isoformat()
                })
                
                # 保存历史数据
                db = next(get_db())
                db.add(MonitorHistory(
                    cpu_temp=hw_status.cpu_temp,
                    fan_speed=target_speed,
                    power_consumption=hw_status.power
                ))
                db.commit()
                
                # 推送 WebSocket 更新
                await self.ws_manager.broadcast({
                    "type": "status_update",
                    "data": self.current_status
                })
                
                logger.info(
                    f"状态监测 - CPU: {hw_status.cpu_temp:.1f}°C | "
                    f"风扇: {target_speed}% | 功耗: {hw_status.power}W"
                )
                
                consecutive_errors = 0
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"监控错误 (#{consecutive_errors}): {e}")
                
                if consecutive_errors >= 10:
                    logger.critical("连续错误过多，暂停监控")
                    await asyncio.sleep(300)  # 暂停5分钟
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(min(60, 2 ** consecutive_errors))
    
    async def stop(self):
        """停止监控服务"""
        self.running = False
        if self.ipmi:
            await self.ipmi.disable_manual_control()
        logger.info("监控服务已停止")
    
    async def reload_settings(self):
        """重新加载配置"""
        await self._load_settings()
        logger.info("配置已重新加载")
```

### 6.4 后端 - services/websocket_service.py

```python
from fastapi import WebSocket
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 连接建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket 连接断开，当前连接数: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接的客户端"""
        if not self.active_connections:
            return
        
        data = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
```


### 6.5 后端 - database.py

```python
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./data/fan_controller.db"

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
    
    # 初始化默认配置
    db = SessionLocal()
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
    
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 6.6 后端 - api/curve.py

```python
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
```

### 6.7 后端 - api/dashboard.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db, MonitorHistory

router = APIRouter()

@router.get("/status")
def get_status():
    """获取当前状态（从监控服务获取）"""
    from main import monitor_service
    return monitor_service.current_status

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
```


### 6.8 后端 - api/logs.py

```python
from fastapi import APIRouter, Query
from typing import Optional
import re
from pathlib import Path

router = APIRouter()

LOG_FILE = Path("/app/data/logs/fan_controller.log")

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
```

### 6.9 后端 - api/settings.py

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db, Settings

router = APIRouter()

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
    updates = request.dict(exclude_none=True)
    
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
    from main import monitor_service
    await monitor_service.reload_settings()
    
    return {"success": True}
```

### 6.10 后端 - requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
websockets==12.0
python-multipart==0.0.6
```


---

## 七、前端代码实现

### 7.1 前端 - package.json

```json
{
  "name": "dell-fan-controller-ui",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.5.0",
    "echarts": "^5.4.3",
    "axios": "^1.6.5",
    "@element-plus/icons-vue": "^2.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

### 7.2 前端 - vite.config.js

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
```

### 7.3 前端 - src/main.js

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import './styles/main.css'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(ElementPlus)
app.mount('#app')
```

### 7.4 前端 - src/App.vue

```vue
<template>
  <el-container class="app-container">
    <el-header>
      <div class="header-content">
        <h1>🖥️ Dell 服务器风扇控制</h1>
        <el-tag :type="statusType">{{ statusText }}</el-tag>
      </div>
    </el-header>
    
    <el-main>
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="仪表盘" name="dashboard">
          <Dashboard />
        </el-tab-pane>
        <el-tab-pane label="风扇曲线" name="curve">
          <CurveEditor />
        </el-tab-pane>
        <el-tab-pane label="系统日志" name="logs">
          <LogViewer />
        </el-tab-pane>
        <el-tab-pane label="系统设置" name="settings">
          <Settings />
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useFanStore } from './stores/fan'
import Dashboard from './components/Dashboard.vue'
import CurveEditor from './components/CurveEditor.vue'
import LogViewer from './components/LogViewer.vue'
import Settings from './components/Settings.vue'

const activeTab = ref('dashboard')
const fanStore = useFanStore()

const statusType = computed(() => {
  return fanStore.status.control_mode === 'manual' ? 'success' : 'warning'
})

const statusText = computed(() => {
  return fanStore.status.control_mode === 'manual' ? '手动控制中' : '自动控制'
})

onMounted(() => {
  fanStore.connectWebSocket()
  fanStore.fetchStatus()
})

onUnmounted(() => {
  fanStore.disconnectWebSocket()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 1.5rem;
}
</style>
```

### 7.5 前端 - src/stores/fan.js

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useFanStore = defineStore('fan', () => {
  const status = ref({
    cpu_temp: 0,
    fan_speed: 0,
    power: 0,
    control_mode: 'auto',
    last_update: null
  })
  
  const curve = ref([])
  const history = ref([])
  const logs = ref([])
  
  let ws = null
  
  // WebSocket 连接
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'status_update') {
        status.value = { ...status.value, ...data.data }
      } else if (data.type === 'log') {
        logs.value.unshift(data.data)
        if (logs.value.length > 200) {
          logs.value.pop()
        }
      }
    }
    
    ws.onclose = () => {
      setTimeout(connectWebSocket, 3000)
    }
  }
  
  function disconnectWebSocket() {
    if (ws) {
      ws.close()
      ws = null
    }
  }
  
  // API 调用
  async function fetchStatus() {
    const { data } = await axios.get('/api/dashboard/status')
    status.value = data
  }
  
  async function fetchCurve() {
    const { data } = await axios.get('/api/curve')
    curve.value = data.points
  }
  
  async function saveCurve(points) {
    await axios.put('/api/curve', { points })
    curve.value = points
  }
  
  async function fetchHistory(range = '1h') {
    const { data } = await axios.get(`/api/dashboard/history?range=${range}`)
    history.value = data.data
  }
  
  async function fetchLogs(params = {}) {
    const { data } = await axios.get('/api/logs', { params })
    logs.value = data.logs
  }
  
  return {
    status,
    curve,
    history,
    logs,
    connectWebSocket,
    disconnectWebSocket,
    fetchStatus,
    fetchCurve,
    saveCurve,
    fetchHistory,
    fetchLogs
  }
})
```


### 7.6 前端 - src/components/Dashboard.vue

```vue
<template>
  <div class="dashboard">
    <!-- 实时状态卡片 -->
    <el-row :gutter="20" class="status-cards">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Cpu /></el-icon>
              <span>CPU 温度</span>
            </div>
          </template>
          <div class="stat-value" :class="tempClass">
            {{ fanStore.status.cpu_temp.toFixed(1) }}°C
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><WindPower /></el-icon>
              <span>风扇转速</span>
            </div>
          </template>
          <div class="stat-value">
            {{ fanStore.status.fan_speed }}%
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Lightning /></el-icon>
              <span>系统功耗</span>
            </div>
          </template>
          <div class="stat-value">
            {{ fanStore.status.power }}W
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 历史趋势图 -->
    <el-card class="chart-card">
      <template #header>
        <div class="chart-header">
          <span>历史趋势</span>
          <el-radio-group v-model="timeRange" size="small" @change="loadHistory">
            <el-radio-button label="1h">1小时</el-radio-button>
            <el-radio-button label="6h">6小时</el-radio-button>
            <el-radio-button label="24h">24小时</el-radio-button>
            <el-radio-button label="7d">7天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="chartRef" class="history-chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useFanStore } from '../stores/fan'
import * as echarts from 'echarts'

const fanStore = useFanStore()
const chartRef = ref(null)
const timeRange = ref('1h')
let chart = null

const tempClass = computed(() => {
  const temp = fanStore.status.cpu_temp
  if (temp >= 80) return 'danger'
  if (temp >= 70) return 'warning'
  return 'normal'
})

function initChart() {
  chart = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  const data = fanStore.history
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['CPU温度', '风扇转速', '功耗']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: '温度/转速',
        min: 0,
        max: 100,
        axisLabel: { formatter: '{value}' }
      },
      {
        type: 'value',
        name: '功耗(W)',
        min: 0,
        axisLabel: { formatter: '{value}W' }
      }
    ],
    series: [
      {
        name: 'CPU温度',
        type: 'line',
        smooth: true,
        data: data.map(d => [d.time, d.cpu_temp]),
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: '风扇转速',
        type: 'line',
        smooth: true,
        data: data.map(d => [d.time, d.fan_speed]),
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '功耗',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: data.map(d => [d.time, d.power]),
        itemStyle: { color: '#67C23A' }
      }
    ]
  }
  
  chart.setOption(option)
}

async function loadHistory() {
  await fanStore.fetchHistory(timeRange.value)
  updateChart()
}

watch(() => fanStore.history, updateChart, { deep: true })

onMounted(() => {
  initChart()
  loadHistory()
  
  window.addEventListener('resize', () => chart?.resize())
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.status-cards {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  text-align: center;
  color: #409EFF;
}

.stat-value.warning { color: #E6A23C; }
.stat-value.danger { color: #F56C6C; }

.chart-card {
  margin-top: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-chart {
  height: 400px;
}
</style>
```


### 7.7 前端 - src/components/CurveEditor.vue (核心组件)

```vue
<template>
  <div class="curve-editor">
    <el-card>
      <template #header>
        <div class="editor-header">
          <span>风扇曲线编辑器</span>
          <div class="actions">
            <el-button type="primary" @click="saveCurve" :loading="saving">
              <el-icon><Check /></el-icon> 保存曲线
            </el-button>
            <el-button @click="resetCurve">
              <el-icon><RefreshRight /></el-icon> 重置
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 曲线图表 -->
      <div ref="chartRef" class="curve-chart"></div>
      
      <!-- 控制点列表 -->
      <el-divider>控制点列表</el-divider>
      
      <el-table :data="points" border size="small">
        <el-table-column label="温度 (°C)" width="200">
          <template #default="{ row, $index }">
            <el-input-number 
              v-model="row.temp" 
              :min="0" 
              :max="100" 
              size="small"
              @change="updateChart"
            />
          </template>
        </el-table-column>
        <el-table-column label="风扇转速 (%)" width="200">
          <template #default="{ row, $index }">
            <el-input-number 
              v-model="row.speed" 
              :min="0" 
              :max="100" 
              size="small"
              @change="updateChart"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ $index }">
            <el-button 
              type="danger" 
              size="small" 
              :disabled="points.length <= 2"
              @click="removePoint($index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-button class="add-btn" @click="addPoint">
        <el-icon><Plus /></el-icon> 添加控制点
      </el-button>
      
      <!-- 当前状态指示 -->
      <el-alert 
        v-if="fanStore.status.cpu_temp > 0"
        :title="`当前温度 ${fanStore.status.cpu_temp.toFixed(1)}°C → 目标转速 ${calculateSpeed(fanStore.status.cpu_temp)}%`"
        type="info"
        show-icon
        :closable="false"
        class="current-status"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useFanStore } from '../stores/fan'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const fanStore = useFanStore()
const chartRef = ref(null)
const points = ref([])
const saving = ref(false)
let chart = null

// 计算给定温度对应的转速
function calculateSpeed(temp) {
  const sorted = [...points.value].sort((a, b) => a.temp - b.temp)
  if (sorted.length === 0) return 20
  
  if (temp <= sorted[0].temp) return sorted[0].speed
  if (temp >= sorted[sorted.length - 1].temp) return sorted[sorted.length - 1].speed
  
  for (let i = 0; i < sorted.length - 1; i++) {
    if (sorted[i].temp <= temp && temp < sorted[i + 1].temp) {
      const t0 = sorted[i].temp, s0 = sorted[i].speed
      const t1 = sorted[i + 1].temp, s1 = sorted[i + 1].speed
      return Math.round(s0 + (temp - t0) * (s1 - s0) / (t1 - t0))
    }
  }
  return sorted[sorted.length - 1].speed
}

function initChart() {
  chart = echarts.init(chartRef.value)
  
  chart.on('dataZoom', updateChart)
  
  // 启用拖拽
  chart.on('click', (params) => {
    if (params.componentType === 'series') {
      // 点击曲线上的点可以选中编辑
    }
  })
  
  updateChart()
}

function updateChart() {
  const sorted = [...points.value].sort((a, b) => a.temp - b.temp)
  
  // 生成平滑曲线数据
  const curveData = []
  for (let t = 0; t <= 100; t++) {
    curveData.push([t, calculateSpeed(t)])
  }
  
  const option = {
    title: {
      text: '温度-转速曲线',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        return `温度: ${p.data[0]}°C<br/>转速: ${p.data[1]}%`
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'value',
      name: '温度 (°C)',
      min: 0,
      max: 100,
      splitLine: { show: true }
    },
    yAxis: {
      type: 'value',
      name: '风扇转速 (%)',
      min: 0,
      max: 100,
      splitLine: { show: true }
    },
    series: [
      {
        name: '风扇曲线',
        type: 'line',
        smooth: true,
        data: curveData,
        lineStyle: { width: 3, color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '控制点',
        type: 'scatter',
        data: sorted.map(p => [p.temp, p.speed]),
        symbolSize: 15,
        itemStyle: { color: '#E6A23C' },
        label: {
          show: true,
          formatter: (p) => `${p.data[0]}°C`,
          position: 'top'
        }
      },
      // 当前温度指示线
      fanStore.status.cpu_temp > 0 ? {
        name: '当前温度',
        type: 'line',
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: '#F56C6C', type: 'dashed', width: 2 },
          data: [{ xAxis: fanStore.status.cpu_temp }],
          label: {
            formatter: `当前: ${fanStore.status.cpu_temp.toFixed(1)}°C`
          }
        }
      } : null
    ].filter(Boolean)
  }
  
  chart.setOption(option, true)
}

function addPoint() {
  const sorted = [...points.value].sort((a, b) => a.temp - b.temp)
  let newTemp = 50
  
  // 找一个合适的温度点
  if (sorted.length > 0) {
    const lastTemp = sorted[sorted.length - 1].temp
    newTemp = Math.min(lastTemp + 10, 100)
  }
  
  points.value.push({ temp: newTemp, speed: 30 })
  updateChart()
}

function removePoint(index) {
  points.value.splice(index, 1)
  updateChart()
}

async function saveCurve() {
  saving.value = true
  try {
    await fanStore.saveCurve(points.value)
    ElMessage.success('风扇曲线已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function resetCurve() {
  await fanStore.fetchCurve()
  points.value = [...fanStore.curve]
  updateChart()
}

watch(() => fanStore.status.cpu_temp, updateChart)

onMounted(async () => {
  await fanStore.fetchCurve()
  points.value = [...fanStore.curve]
  initChart()
  
  window.addEventListener('resize', () => chart?.resize())
})
</script>

<style scoped>
.curve-editor {
  padding: 20px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.curve-chart {
  height: 400px;
  margin-bottom: 20px;
}

.add-btn {
  margin-top: 15px;
  width: 100%;
}

.current-status {
  margin-top: 20px;
}
</style>
```


### 7.8 前端 - src/components/LogViewer.vue

```vue
<template>
  <div class="log-viewer">
    <el-card>
      <template #header>
        <div class="log-header">
          <span>系统日志</span>
          <div class="filters">
            <el-select v-model="levelFilter" placeholder="日志级别" clearable size="small" @change="loadLogs">
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
            <el-input 
              v-model="searchKeyword" 
              placeholder="搜索关键词" 
              size="small" 
              clearable
              @keyup.enter="loadLogs"
              style="width: 200px"
            />
            <el-button size="small" @click="loadLogs">
              <el-icon><Search /></el-icon>
            </el-button>
            <el-button size="small" @click="clearFilters">清除</el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="fanStore.logs" 
        height="500" 
        stripe 
        size="small"
        :row-class-name="getRowClass"
      >
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" show-overflow-tooltip />
      </el-table>
      
      <div class="log-footer">
        <span>共 {{ fanStore.logs.length }} 条日志</span>
        <el-button size="small" @click="loadLogs">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useFanStore } from '../stores/fan'

const fanStore = useFanStore()
const levelFilter = ref('')
const searchKeyword = ref('')

function getLevelType(level) {
  const types = {
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'danger',
    'CRITICAL': 'danger'
  }
  return types[level] || 'info'
}

function getRowClass({ row }) {
  if (row.level === 'ERROR' || row.level === 'CRITICAL') {
    return 'error-row'
  }
  if (row.level === 'WARNING') {
    return 'warning-row'
  }
  return ''
}

async function loadLogs() {
  await fanStore.fetchLogs({
    level: levelFilter.value || undefined,
    search: searchKeyword.value || undefined,
    limit: 200
  })
}

function clearFilters() {
  levelFilter.value = ''
  searchKeyword.value = ''
  loadLogs()
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.log-viewer {
  padding: 20px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  color: #909399;
}

:deep(.error-row) {
  background-color: #fef0f0 !important;
}

:deep(.warning-row) {
  background-color: #fdf6ec !important;
}
</style>
```

### 7.9 前端 - src/components/Settings.vue

```vue
<template>
  <div class="settings">
    <el-card>
      <template #header>
        <span>iDRAC 连接设置</span>
      </template>
      
      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item label="iDRAC 地址" prop="ip_address">
          <el-input v-model="form.ip_address" placeholder="192.168.1.100" />
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="root" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="输入新密码或留空保持不变" />
        </el-form-item>
        
        <el-form-item label="监控间隔" prop="interval">
          <el-input-number v-model="form.interval" :min="5" :max="300" :step="5" />
          <span class="unit">秒</span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
          <el-button @click="loadSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="danger-zone">
      <template #header>
        <span style="color: #F56C6C">危险操作</span>
      </template>
      
      <el-button type="warning" @click="restoreAutoControl">
        恢复自动风扇控制
      </el-button>
      <p class="hint">将风扇控制权交还给 iDRAC 自动管理</p>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const formRef = ref(null)
const saving = ref(false)

const form = reactive({
  ip_address: '',
  username: '',
  password: '',
  interval: 30
})

const rules = {
  ip_address: [
    { required: true, message: '请输入 iDRAC 地址', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  interval: [
    { required: true, message: '请设置监控间隔', trigger: 'blur' }
  ]
}

async function loadSettings() {
  try {
    const { data } = await axios.get('/api/settings')
    form.ip_address = data.ip_address
    form.username = data.username
    form.password = ''
    form.interval = data.interval
  } catch (error) {
    ElMessage.error('加载设置失败')
  }
}

async function saveSettings() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.password) {
      delete payload.password
    }
    
    await axios.put('/api/settings', payload)
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function restoreAutoControl() {
  try {
    await ElMessageBox.confirm(
      '确定要恢复自动风扇控制吗？这将停止手动控制。',
      '确认操作',
      { type: 'warning' }
    )
    
    await axios.post('/api/dashboard/restore-auto')
    ElMessage.success('已恢复自动控制')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings {
  padding: 20px;
  max-width: 600px;
}

.unit {
  margin-left: 10px;
  color: #909399;
}

.danger-zone {
  margin-top: 20px;
}

.hint {
  margin-top: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
```

### 7.10 前端 - src/styles/main.css

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f7fa;
}

.el-main {
  padding: 20px;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
```


---

## 八、Docker 部署配置

### 8.1 docker-compose.yml

```yaml
version: '3.8'

services:
  dell-fan-controller:
    build: .
    container_name: dell-fan-controller
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/dashboard/status"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 8.2 Dockerfile (多阶段构建)

```dockerfile
# ============ 阶段1: 构建前端 ============
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ============ 阶段2: 最终镜像 ============
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    ipmitool \
    alien \
    rpm \
    curl \
    libssl3 \
    && ln -s /usr/lib/x86_64-linux-gnu/libssl.so.3 /usr/lib/x86_64-linux-gnu/libssl.so \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Dell iDRAC 工具
ARG DRACTOOLS_PKG=DellEMC-iDRACTools-Web-LX-9.4.0-3732_A00.tar.gz
COPY ${DRACTOOLS_PKG} /tmp/
RUN tar -xzvf /tmp/${DRACTOOLS_PKG} -C /tmp/ && \
    cd /tmp/iDRACTools/racadm/RHEL8/x86_64/ && \
    alien --scripts *.rpm && \
    dpkg -i *.deb && \
    ln -s /opt/dell/srvadmin/bin/idracadm7 /usr/local/bin/racadm && \
    rm -rf /tmp/*

# 安装 Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/static

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 创建数据目录
RUN mkdir -p /app/data/logs

# 复制启动脚本
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 80

CMD ["./start.sh"]
```

### 8.3 nginx.conf

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    server {
        listen 80;
        server_name _;

        # 前端静态文件
        location / {
            root /app/static;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # WebSocket 代理
        location /ws {
            proxy_pass http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 86400;
        }
    }
}
```

### 8.4 start.sh (新版)

```bash
#!/bin/bash
set -e

echo "=== Dell Fan Controller Starting ==="

# 创建必要目录
mkdir -p /app/data/logs

# 启动 Nginx
echo "Starting Nginx..."
nginx

# 启动后端服务
echo "Starting Backend API..."
cd /app/backend
exec uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info
```


---

## 九、日志系统优化

### 9.1 改进点

| 原有问题 | 优化方案 |
|---------|---------|
| 只有文件日志 | 增加数据库存储 + WebSocket 实时推送 |
| 无法过滤搜索 | 支持级别过滤、关键词搜索 |
| 10秒刷新整页 | WebSocket 实时推送，无需刷新 |
| 日志格式单一 | 结构化日志，便于解析展示 |

### 9.2 日志配置

```python
# backend/logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("/app/data/logs")
LOG_FILE = LOG_DIR / "fan_controller.log"

def setup_logging(ws_manager=None):
    """配置日志系统"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 创建根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
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
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.ws_manager.broadcast(message))
        except Exception:
            pass
```

---

## 十、控制逻辑优化

### 10.1 改进点

| 原有问题 | 优化方案 |
|---------|---------|
| 同步阻塞调用 | 改用 asyncio 异步执行 |
| 配置5分钟重载 | 配置变更即时生效 |
| 硬编码错误阈值 | 可配置的错误处理策略 |
| 无状态持久化 | 历史数据存入数据库 |

### 10.2 风扇控制策略增强

```python
# backend/services/fan_strategy.py
from dataclasses import dataclass
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class FanControlResult:
    target_speed: int
    reason: str
    is_emergency: bool = False

class FanStrategy:
    """风扇控制策略"""
    
    def __init__(self):
        self.min_speed = 10          # 最低转速
        self.max_speed = 100         # 最高转速
        self.emergency_temp = 90     # 紧急温度阈值
        self.emergency_speed = 100   # 紧急转速
        self.hysteresis = 2          # 滞后温度（防止频繁切换）
        self._last_speed = None
    
    def calculate(
        self, 
        temp: float, 
        curve: List[Tuple[int, int]],
        power: Optional[int] = None
    ) -> FanControlResult:
        """
        计算目标风扇转速
        
        Args:
            temp: 当前温度
            curve: 温度-转速曲线 [(temp, speed), ...]
            power: 当前功耗（可选，用于功耗感知调速）
        
        Returns:
            FanControlResult: 控制结果
        """
        # 紧急保护
        if temp >= self.emergency_temp:
            logger.warning(f"温度过高 ({temp}°C)，启动紧急冷却")
            return FanControlResult(
                target_speed=self.emergency_speed,
                reason="紧急冷却",
                is_emergency=True
            )
        
        # 根据曲线计算基础转速
        base_speed = self._interpolate(temp, curve)
        
        # 应用滞后逻辑（防止频繁切换）
        if self._last_speed is not None:
            speed_diff = abs(base_speed - self._last_speed)
            if speed_diff < 3:  # 变化小于3%时保持不变
                base_speed = self._last_speed
        
        # 功耗感知调整（可选）
        if power and power > 300:
            # 高功耗时适当提高转速
            power_boost = min(10, (power - 300) // 50)
            base_speed = min(self.max_speed, base_speed + power_boost)
        
        # 限制范围
        final_speed = max(self.min_speed, min(self.max_speed, base_speed))
        self._last_speed = final_speed
        
        return FanControlResult(
            target_speed=final_speed,
            reason=f"曲线计算: {temp}°C → {final_speed}%"
        )
    
    def _interpolate(self, temp: float, curve: List[Tuple[int, int]]) -> int:
        """线性插值计算"""
        if not curve:
            return 20
        
        curve = sorted(curve, key=lambda x: x[0])
        
        if temp <= curve[0][0]:
            return curve[0][1]
        if temp >= curve[-1][0]:
            return curve[-1][1]
        
        for i in range(len(curve) - 1):
            t0, s0 = curve[i]
            t1, s1 = curve[i + 1]
            if t0 <= temp < t1:
                return int(s0 + (temp - t0) * (s1 - s0) / (t1 - t0))
        
        return curve[-1][1]
```


---

## 十一、部署指南

### 11.1 快速部署

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd dell-fan-controller

# 2. 准备 Dell iDRAC 工具包
# 从 Dell 官网下载 DellEMC-iDRACTools-Web-LX-9.4.0-3732_A00.tar.gz
# 放置到项目根目录

# 3. 构建并启动
docker-compose up -d --build

# 4. 访问 Web 界面
# http://your-server-ip:8080
```

### 11.2 首次配置

1. 打开浏览器访问 `http://your-server-ip:8080`
2. 进入「系统设置」页面
3. 填写 iDRAC 连接信息：
   - IP 地址：服务器 iDRAC 的 IP
   - 用户名：iDRAC 管理员账号
   - 密码：iDRAC 密码
   - 监控间隔：建议 30 秒
4. 保存设置
5. 进入「风扇曲线」页面，根据需要调整温度-转速曲线
6. 在「仪表盘」查看实时状态

### 11.3 数据持久化

```
./data/
├── fan_controller.db    # SQLite 数据库（配置、历史数据）
└── logs/
    └── fan_controller.log  # 日志文件
```

建议定期备份 `./data` 目录。

### 11.4 常用命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务（会自动恢复自动风扇控制）
docker-compose down

# 更新部署
docker-compose pull
docker-compose up -d --build
```

---

## 十二、开发计划

### 12.1 实施阶段

| 阶段 | 任务 | 预计时间 |
|-----|------|---------|
| 1 | 后端基础架构（FastAPI + SQLite） | 2天 |
| 2 | IPMI 服务重构（异步化） | 1天 |
| 3 | 监控服务 + WebSocket | 1天 |
| 4 | 前端框架搭建（Vue3 + Element Plus） | 1天 |
| 5 | 仪表盘组件 | 1天 |
| 6 | 曲线编辑器组件 | 2天 |
| 7 | 日志查看器 + 设置页面 | 1天 |
| 8 | Docker 多阶段构建 | 0.5天 |
| 9 | 测试 + 文档 | 1天 |

**总计：约 10.5 天**

### 12.2 文件创建清单

```
新建文件:
├── docker-compose.yml
├── nginx.conf
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── logging_config.py
│   ├── requirements.txt
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── curve.py
│   │   ├── logs.py
│   │   └── settings.py
│   └── services/
│       ├── __init__.py
│       ├── ipmi_service.py
│       ├── monitor_service.py
│       ├── websocket_service.py
│       └── fan_strategy.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── stores/
│       │   └── fan.js
│       ├── components/
│       │   ├── Dashboard.vue
│       │   ├── CurveEditor.vue
│       │   ├── LogViewer.vue
│       │   └── Settings.vue
│       └── styles/
│           └── main.css

修改文件:
├── Dockerfile (重写为多阶段构建)
└── start.sh (更新启动逻辑)

删除文件:
├── fan_controller.py (功能迁移到 backend/)
├── web_logger.py (功能迁移到前端)
└── config/config.json (迁移到数据库)
```

---

## 十三、总结

本重构方案将原有的简单脚本升级为现代化的前后端分离架构：

1. **用户体验提升**：从简陋的 HTML 页面升级为响应式 SPA，支持实时数据更新
2. **可视化曲线编辑**：直观的图表编辑器，支持拖拽和实时预览
3. **数据持久化**：历史数据存储，支持趋势分析
4. **运维友好**：一键 Docker 部署，配置热更新
5. **代码质量**：异步架构，结构清晰，易于维护扩展

按照本文档的设计和代码实现，可以完整构建出一个功能完善的 Dell 服务器风扇控制系统。
