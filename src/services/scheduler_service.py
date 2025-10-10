"""
Enhanced Scheduler Service

Production-ready scheduler with error recovery, persistence,
job management, and comprehensive monitoring.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler import events

from src.config import config
from src.database.operations import get_session, ReminderOperations, SystemLogOperations

logger = logging.getLogger(__name__)


class SchedulerService:
    """Enhanced scheduler service for reminder management."""
    
    def __init__(self, bot):
        """Initialize scheduler service."""
        self.bot = bot
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._job_stats = {
            'executed': 0,
            'errors': 0,
            'missed': 0,
            'scheduled': 0
        }
        
        # Configure scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': True,
            'max_instances': 3,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=config.SCHEDULER_TIMEZONE
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener, 
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED
        )
    
    async def start(self) -> None:
        """Start the scheduler."""
        try:
            self.scheduler.start()
            
            # Schedule cleanup job
            self.scheduler.add_job(
                self._cleanup_old_jobs,
                'interval',
                hours=config.CLEANUP_INTERVAL_HOURS,
                id='cleanup_jobs',
                replace_existing=True
            )
            
            logger.info("✅ Scheduler started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("✅ Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    
    async def schedule_reminder(self, reminder_id: int, scheduled_time: datetime) -> bool:
        """Schedule a reminder for delivery."""
        try:
            job_id = f"reminder_{reminder_id}"
            
            # Remove existing job if present
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Add new job
            self.scheduler.add_job(
                self._send_reminder,
                'date',
                run_date=scheduled_time,
                args=[reminder_id],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=300  # 5 minutes
            )
            
            self._job_stats['scheduled'] += 1
            logger.info(f"📅 Scheduled reminder {reminder_id} for {scheduled_time}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule reminder {reminder_id}: {e}")
            
            async with get_session() as session:
                await SystemLogOperations.create_log(
                    session=session,
                    level="ERROR",
                    message=f"Failed to schedule reminder: {str(e)}",
                    module="scheduler",
                    reminder_id=reminder_id
                )
            
            return False
    
    async def reschedule_reminder(self, reminder_id: int, new_time: datetime) -> bool:
        """Reschedule an existing reminder."""
        try:
            job_id = f"reminder_{reminder_id}"
            
            job = self.scheduler.get_job(job_id)
            if job:
                job.reschedule('date', run_date=new_time)
                logger.info(f"📅 Rescheduled reminder {reminder_id} to {new_time}")
                return True
            else:
                # Job doesn't exist, create new one
                return await self.schedule_reminder(reminder_id, new_time)
                
        except Exception as e:
            logger.error(f"❌ Failed to reschedule reminder {reminder_id}: {e}")
            return False
    
    async def cancel_reminder(self, reminder_id: int) -> bool:
        """Cancel a scheduled reminder."""
        try:
            job_id = f"reminder_{reminder_id}"
            
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"❌ Cancelled reminder {reminder_id}")
                return True
            
            return False  # Job didn't exist
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel reminder {reminder_id}: {e}")
            return False
    
    async def load_pending_reminders(self) -> int:
        """Load pending reminders from database and schedule them."""
        try:
            count = 0
            now = datetime.utcnow()
            
            async with get_session() as session:
                # Get reminders scheduled for the future that haven't been sent
                future_time = now + timedelta(days=365)  # Load reminders up to 1 year ahead
                pending_reminders = await ReminderOperations.get_pending_reminders(
                    session, future_time
                )
                
                for reminder in pending_reminders:
                    # Only schedule if time is in the future
                    if reminder.scheduled_time > now:
                        success = await self.schedule_reminder(
                            reminder.id, 
                            reminder.scheduled_time
                        )
                        if success:
                            count += 1
                    else:
                        # Mark overdue reminders as missed
                        logger.warning(f"Reminder {reminder.id} is overdue, marking as missed")
                        await self._mark_reminder_missed(reminder.id)
            
            logger.info(f"📥 Loaded {count} pending reminders")
            return count
            
        except Exception as e:
            logger.error(f"❌ Failed to load pending reminders: {e}")
            return 0
    
    async def _send_reminder(self, reminder_id: int) -> None:
        """Send reminder to user."""
        try:
            async with get_session() as session:
                reminder = await ReminderOperations.get_reminder_by_id(session, reminder_id)
                
                if not reminder:
                    logger.warning(f"Reminder {reminder_id} not found")
                    return
                
                if reminder.is_sent:
                    logger.warning(f"Reminder {reminder_id} already sent")
                    return
                
                # Format reminder message
                message_text = self._format_reminder_message(reminder)
                
                # Send message to user
                try:
                    await self.bot.send_message(
                        chat_id=reminder.user.telegram_id,
                        text=message_text,
                        parse_mode="Markdown"
                    )
                    
                    # Mark as sent
                    await ReminderOperations.mark_reminder_sent(session, reminder_id)
                    
                    logger.info(f"✅ Sent reminder {reminder_id} to user {reminder.user.telegram_id}")
                    
                    # Log success
                    await SystemLogOperations.create_log(
                        session=session,
                        level="INFO",
                        message=f"Reminder sent successfully",
                        module="scheduler",
                        user_id=reminder.user_id,
                        reminder_id=reminder_id
                    )
                    
                except Exception as send_error:
                    logger.error(f"❌ Failed to send reminder {reminder_id}: {send_error}")
                    
                    # Log delivery failure
                    await SystemLogOperations.create_log(
                        session=session,
                        level="ERROR",
                        message=f"Failed to deliver reminder: {str(send_error)}",
                        module="scheduler",
                        user_id=reminder.user_id,
                        reminder_id=reminder_id
                    )
                    
                    # Retry logic could be implemented here
                    
        except Exception as e:
            logger.error(f"❌ Error in _send_reminder for {reminder_id}: {e}")
    
    def _format_reminder_message(self, reminder) -> str:
        """Format reminder message for delivery."""
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        
        message = f"🔔 **НАПОМИНАНИЕ!**\n\n"
        message += f"📝 {reminder.title}\n\n"
        
        if reminder.description:
            message += f"📄 {reminder.description}\n\n"
        
        message += f"⏰ {time_str}\n"
        message += f"🆔 #{reminder.id}"
        
        # Add category if present
        if reminder.category:
            category_icons = {
                'work': '💼',
                'health': '🏥', 
                'shopping': '🛒',
                'family': '👨‍👩‍👧‍👦',
                'personal': '🎯'
            }
            icon = category_icons.get(reminder.category.lower(), '📁')
            message += f"\n{icon} {reminder.category.title()}"
        
        return message
    
    async def _mark_reminder_missed(self, reminder_id: int) -> None:
        """Mark reminder as missed (overdue)."""
        try:
            async with get_session() as session:
                # Log as missed
                await SystemLogOperations.create_log(
                    session=session,
                    level="WARNING",
                    message=f"Reminder missed (overdue)",
                    module="scheduler",
                    reminder_id=reminder_id
                )
                
                # Update statistics could be added here
                
        except Exception as e:
            logger.error(f"❌ Error marking reminder {reminder_id} as missed: {e}")
    
    def _job_executed_listener(self, event) -> None:
        """Handle scheduler events."""
        if event.exception:
            self._job_stats['errors'] += 1
            logger.error(f"Job {event.job_id} crashed: {event.exception}")
        else:
            if event.code == events.EVENT_JOB_EXECUTED:
                self._job_stats['executed'] += 1
                logger.debug(f"Job {event.job_id} executed successfully")
            elif event.code == events.EVENT_JOB_MISSED:
                self._job_stats['missed'] += 1
                logger.warning(f"Job {event.job_id} missed")
    
    async def _cleanup_old_jobs(self) -> None:
        """Clean up old completed jobs and data."""
        try:
            # Remove old system logs
            async with get_session() as session:
                deleted_logs = await SystemLogOperations.cleanup_old_logs(session, days_to_keep=30)
                if deleted_logs > 0:
                    logger.info(f"🧹 Cleaned up {deleted_logs} old log entries")
            
            # Job cleanup is automatic with MemoryJobStore
            logger.debug("🧹 Cleanup job completed")
            
        except Exception as e:
            logger.error(f"❌ Error in cleanup job: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        active_jobs = len(self.scheduler.get_jobs())
        
        return {
            'running': self.scheduler.running,
            'active_jobs': active_jobs,
            'stats': self._job_stats.copy(),
            'timezone': str(self.scheduler.timezone)
        }
    
    def get_job_info(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific job."""
        job_id = f"reminder_{reminder_id}"
        job = self.scheduler.get_job(job_id)
        
        if not job:
            return None
        
        return {
            'id': job.id,
            'next_run': job.next_run_time,
            'trigger': str(job.trigger),
            'args': job.args,
            'kwargs': job.kwargs
        }


# Global scheduler instance
scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service(bot) -> SchedulerService:
    """Get or create scheduler service instance."""
    global scheduler_service
    if scheduler_service is None:
        scheduler_service = SchedulerService(bot)
    return scheduler_service
