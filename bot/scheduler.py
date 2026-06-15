import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from duas import get_dua_of_day
from storage import get_all_subscribers, get_subscriber_time, get_dua_enabled

logger = logging.getLogger(__name__)


async def send_daily_dua(bot, chat_id: int):
    enabled = await get_dua_enabled(chat_id)
    if not enabled:
        return

    dua = get_dua_of_day()
    from datetime import datetime, timezone
    date_str = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    text = (
        f"☀️ *Дуа дня — {date_str}*\n\n"
        f"*{dua['title']}*\n\n"
        f"{dua['arabic']}\n\n"
        f"*Транслитерация:*\n_{dua['transliteration']}_\n\n"
        f"*Перевод:*\n{dua['translation']}\n\n"
        f"📖 {dua['source']}\n\n"
        f"_/duaoff — отключить дуа дня_"
    )
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            disable_notification=True,
        )
        logger.info(f"Sent daily dua to {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send dua to {chat_id}: {e}")


def create_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    return scheduler


async def reschedule_user(scheduler: AsyncIOScheduler, bot, chat_id: int):
    job_id = f"dua_{chat_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    time_str = await get_subscriber_time(chat_id)
    hour, minute = map(int, time_str.split(":"))

    scheduler.add_job(
        send_daily_dua,
        CronTrigger(hour=hour, minute=minute, timezone="UTC"),
        args=[bot, chat_id],
        id=job_id,
        replace_existing=True,
    )
    logger.info(f"Scheduled dua for {chat_id} at {time_str} UTC")


async def load_all_schedules(scheduler: AsyncIOScheduler, bot):
    subscribers = await get_all_subscribers()
    for chat_id, time_str in subscribers:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(
            send_daily_dua,
            CronTrigger(hour=hour, minute=minute, timezone="UTC"),
            args=[bot, chat_id],
            id=f"dua_{chat_id}",
            replace_existing=True,
        )
    logger.info(f"Loaded {len(subscribers)} scheduled reminders")


def remove_user_schedule(scheduler: AsyncIOScheduler, chat_id: int):
    job_id = f"dua_{chat_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed schedule for {chat_id}")
