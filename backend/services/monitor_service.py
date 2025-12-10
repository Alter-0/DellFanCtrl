import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from services.ipmi_service import IPMIService
from services.websocket_service import WebSocketManager
from database import SessionLocal, MonitorHistory, FanCurve, Settings, utcnow

logger = logging.getLogger(__name__)

class MonitorService:
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.ipmi: Optional[IPMIService] = None
        self.running = False
        self.interval = 30
        self.current_status = {
            "cpu_temp": 0,
            "fan_speed": 0,
            "power": 0,
            "control_mode": "auto"
        }
        # 风扇曲线缓存
        self._fan_curve_cache: Optional[List[Tuple[int, int]]] = None
    
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

    def _load_settings_sync(self):
        """从数据库加载配置（同步版本）"""
        db = SessionLocal()
        try:
            settings = {s.key: s.value for s in db.query(Settings).all()}
            
            self.ipmi = IPMIService(
                ip=settings.get('ip_address', ''),
                username=settings.get('username', ''),
                password=settings.get('password', '')
            )
            self.interval = int(settings.get('interval', 30))
        finally:
            db.close()
    
    def _get_fan_curve_sync(self) -> List[Tuple[int, int]]:
        """获取风扇曲线配置（同步版本，带缓存）"""
        if self._fan_curve_cache is not None:
            return self._fan_curve_cache
        
        db = SessionLocal()
        try:
            points = db.query(FanCurve).order_by(FanCurve.temperature).all()
            self._fan_curve_cache = [(p.temperature, p.fan_speed) for p in points]
            return self._fan_curve_cache
        finally:
            db.close()
    
    def invalidate_curve_cache(self):
        """使风扇曲线缓存失效，下次查询时重新加载"""
        self._fan_curve_cache = None
        logger.info("风扇曲线缓存已清除")
    
    async def start(self):
        """启动监控服务"""
        self.running = True
        try:
            self._load_settings_sync()
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return
        
        if not self.ipmi or not self.ipmi.ip:
            logger.warning("未配置 iDRAC 地址，监控服务等待配置...")
            # 等待配置，每30秒检查一次
            while self.running and (not self.ipmi or not self.ipmi.ip):
                await asyncio.sleep(30)
                try:
                    self._load_settings_sync()
                except Exception:
                    pass
            if not self.running:
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
                curve = self._get_fan_curve_sync()
                target_speed = self.calculate_fan_speed(hw_status.cpu_temp, curve)
                
                # 设置风扇转速
                await self.ipmi.set_fan_speed(target_speed)
                
                # 更新当前状态
                self.current_status.update({
                    "cpu_temp": hw_status.cpu_temp,
                    "fan_speed": target_speed,
                    "power": hw_status.power,
                    "last_update": utcnow().isoformat()
                })
                
                # 保存历史数据
                db = SessionLocal()
                try:
                    db.add(MonitorHistory(
                        cpu_temp=hw_status.cpu_temp,
                        fan_speed=target_speed,
                        power_consumption=hw_status.power
                    ))
                    db.commit()
                finally:
                    db.close()
                
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
        self._load_settings_sync()
        logger.info("配置已重新加载")
    
    async def restore_auto_control(self):
        """恢复自动控制"""
        if self.ipmi:
            await self.ipmi.disable_manual_control()
            self.current_status["control_mode"] = "auto"
