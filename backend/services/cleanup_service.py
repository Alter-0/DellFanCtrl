"""
Data Cleanup Service for automatic removal of old MonitorHistory records.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from database import SessionLocal, MonitorHistory, Settings, utcnow

logger = logging.getLogger(__name__)


class DataCleanupService:
    """Service responsible for periodic cleanup of expired historical data."""
    
    DEFAULT_RETENTION_DAYS = 30
    
    def __init__(self, retention_days: int = DEFAULT_RETENTION_DAYS):
        """Initialize cleanup service with retention period.
        
        Args:
            retention_days: Number of days to retain data. Default is 30.
        """
        self._retention_days = retention_days
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    @property
    def retention_days(self) -> int:
        """Get current retention period in days."""
        return self._retention_days
    
    def set_retention_days(self, days: int) -> None:
        """Update the retention period for subsequent cleanups.
        
        Args:
            days: New retention period in days.
        """
        self._retention_days = days
        logger.info(f"数据保留期限已更新为 {days} 天")
    
    async def cleanup(self) -> int:
        """Execute cleanup operation, deleting records older than retention period.
        
        Returns:
            Number of deleted records.
        """
        cutoff_date = utcnow() - timedelta(days=self._retention_days)
        
        db = SessionLocal()
        try:
            # Query and delete old records
            old_records = db.query(MonitorHistory).filter(
                MonitorHistory.recorded_at < cutoff_date
            )
            deleted_count = old_records.count()
            old_records.delete(synchronize_session=False)
            db.commit()
            
            logger.info(f"数据清理完成，删除了 {deleted_count} 条过期记录")
            return deleted_count
        except Exception as e:
            db.rollback()
            logger.error(f"数据清理失败: {e}")
            raise
        finally:
            db.close()
    
    async def start(self) -> None:
        """Start the periodic cleanup task (runs daily at 3:00 AM)."""
        self._running = True
        self._task = asyncio.create_task(self._run_periodic())
        logger.info(f"数据清理服务已启动，保留期限: {self._retention_days} 天")
    
    async def stop(self) -> None:
        """Stop the cleanup service."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("数据清理服务已停止")
    
    async def _run_periodic(self) -> None:
        """Internal method to run cleanup periodically."""
        while self._running:
            try:
                # Calculate time until next 3:00 AM (UTC)
                now = utcnow()
                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
                if now >= next_run:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"下次数据清理将在 {next_run.strftime('%Y-%m-%d %H:%M:%S')} 执行")
                
                await asyncio.sleep(wait_seconds)
                
                if self._running:
                    await self.cleanup()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务执行错误: {e}")
                # Wait an hour before retrying on error
                await asyncio.sleep(3600)
