import logging
import random
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from duas import DUAS
from storage import get_all_subscribers, get_subscriber_time

logger = logging.getLogger(__name__)


async def send_daily_dua(bot, chat_id: int):
    dua = random.choice(DUAS)
    text = (
        f"🌙 *Daily Dua Reminder*\n\n"
        f"*{dua['title']}*\n\n"
        f"*Arabic:*\n{dua['arabic']}\n\n"
        f"*Transliteration:*\n_{dua['transliteration']}_\n\n"
        f"*Translation:*\n{dua['translation']}\n\n"
        f"📖 Source: {dua['source']}"
    )
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
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
