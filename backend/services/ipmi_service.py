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
