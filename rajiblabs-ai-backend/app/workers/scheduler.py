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
    # Profile Intelligence Agent — daily 06:00 Asia/Kolkata
    try:
        from app.services.profile_agent import run_profile_agent
        _sched.add_job(lambda: run_profile_agent(triggered_by="scheduler"), CronTrigger(hour=6, minute=0),
                       id="profile-agent", replace_existing=True, max_instances=1)
        log.info("Scheduler added profile-agent daily 06:00 %s", s.app_timezone)
    except Exception as e:
        log.warning("Profile agent scheduler not added: %s", e)
    # Marketing Intelligence Agent — daily 09:00 Asia/Kolkata (draft-first;
    # the agent itself enforces audience, cadence, duplicate and approval gates)
    try:
        from app.services.marketing_agent import run_daily as _mkt_daily
        _sched.add_job(_mkt_daily, CronTrigger(hour=9, minute=0),
                       id="marketing-agent", replace_existing=True, max_instances=1,
                       kwargs={"triggered_by": "scheduler"})
        log.info("Scheduler added marketing-agent daily 09:00 %s", s.app_timezone)
    except Exception as e:
        log.warning("Marketing agent scheduler not added: %s", e)
    # Learning Agent — daily 06:00 Asia/Kolkata (mentor content, hash-guarded, RAG-synced)
    try:
        from app.services.learning_agent import run_daily as _learn_daily
        _sched.add_job(_learn_daily, CronTrigger(hour=6, minute=0),
                       id="learning-agent", replace_existing=True, max_instances=1,
                       kwargs={"triggered_by": "scheduler"})
        log.info("Scheduler added learning-agent daily 06:00 %s", s.app_timezone)
    except Exception as e:
        log.warning("Learning agent scheduler not added: %s", e)
    _sched.start()
    log.info("Scheduler started daily %02d:%02d %s", s.daily_agent_hour, s.daily_agent_minute, s.app_timezone)
    return _sched
