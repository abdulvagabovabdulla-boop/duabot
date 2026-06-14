import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from handlers import router
from scheduler import create_scheduler, load_all_schedules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    scheduler = create_scheduler(bot)
    await load_all_schedules(scheduler, bot)
    scheduler.start()
    logger.info("Scheduler started")

    await bot.set_my_commands([
        BotCommand(command="subscribe", description="Подписаться на ежедневные дуа"),
        BotCommand(command="unsubscribe", description="Отписаться от напоминаний"),
        BotCommand(command="settime", description="Установить время отправки (UTC)"),
        BotCommand(command="dua", description="Получить случайную дуа прямо сейчас"),
        BotCommand(command="status", description="Проверить статус подписки"),
        BotCommand(command="help", description="Список команд"),
    ])
    logger.info("Bot commands menu set")

    dp.include_router(router)

    dp.update.middleware.register(SchedulerMiddleware(scheduler, bot))

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot, allowed_updates=["message"])
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot stopped")


class SchedulerMiddleware:
    def __init__(self, scheduler, bot):
        self.scheduler = scheduler
        self.bot = bot

    async def __call__(self, handler, event, data):
        data["scheduler"] = self.scheduler
        data["bot"] = self.bot
        return await handler(event, data)


if __name__ == "__main__":
    asyncio.run(main())
