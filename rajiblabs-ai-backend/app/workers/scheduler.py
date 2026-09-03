"""APScheduler daily agent (02:00 Asia/Kolkata default) + manual trigger."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import get_settings

log = logging.getLogger("rajiblabs")
_sched: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    global _sched
    if _sched:
        return _sched
    s = get_settings()
    _sched = AsyncIOScheduler(timezone=s.app_timezone)
    from app.agents.daily_agent import run_daily_agent
    _sched.add_job(run_daily_agent, CronTrigger(hour=s.daily_agent_hour, minute=s.daily_agent_minute),
                   id="daily-agent", replace_existing=True, max_instances=1)
    _sched.start()
    log.info("Scheduler started daily %02d:%02d %s", s.daily_agent_hour, s.daily_agent_minute, s.app_timezone)
    return _sched
