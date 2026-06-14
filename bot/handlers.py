import random
import re
import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from duas import DUAS, MORNING_ADHKAR, EVENING_ADHKAR, AFTER_PRAYER_DUAS
from storage import (
    add_subscriber,
    remove_subscriber,
    is_subscribed,
    get_subscriber_time,
    set_subscriber_time,
    get_all_subscribers,
)
from scheduler import reschedule_user, remove_user_schedule

logger = logging.getLogger(__name__)
router = Router()

ADMIN_ID = 6462821940


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌅 Утренние азкары", callback_data="cat_morning"),
            InlineKeyboardButton(text="🌆 Вечерние азкары", callback_data="cat_evening"),
        ],
        [
            InlineKeyboardButton(text="🕌 Дуа после намаза", callback_data="cat_after_prayer"),
            InlineKeyboardButton(text="🎲 Случайная дуа", callback_data="cat_random"),
        ],
    ])


def format_dua(dua: dict, heading: str = "🌙 Дуа для тебя") -> str:
    return (
        f"{heading}\n\n"
        f"*{dua['title']}*\n\n"
        f"*Арабский:*\n{dua['arabic']}\n\n"
        f"*Транслитерация:*\n_{dua['transliteration']}_\n\n"
        f"*Перевод:*\n{dua['translation']}\n\n"
        f"📖 Источник: {dua['source']}"
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🌙 *Ас-саламу алейкум!*\n\n"
        "Добро пожаловать в *Бот ежедневных дуа*. Каждый день я буду отправлять тебе красивую дуа, чтобы твоё сердце оставалось в связи с Аллахом ﷻ.\n\n"
        "📋 *Команды:*\n"
        "/subscribe — Подписаться на ежедневные дуа\n"
        "/unsubscribe — Отписаться от напоминаний\n"
        "/settime — Установить время отправки (UTC)\n"
        "/dua — Получить случайную дуа прямо сейчас\n"
        "/adhkar — Азкары и дуа по категориям\n"
        "/status — Проверить статус подписки\n"
        "/help — Показать это сообщение снова\n\n"
        "Используй /subscribe, чтобы начать 🤲",
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🌙 *Бот ежедневных дуа*\n\n"
        "📋 *Доступные команды:*\n"
        "/subscribe — Подписаться на ежедневные дуа\n"
        "/unsubscribe — Отписаться от напоминаний\n"
        "/settime — Установить время отправки (UTC)\n"
        "/dua — Получить случайную дуа прямо сейчас\n"
        "/adhkar — Азкары и дуа по категориям\n"
        "/status — Проверить статус подписки\n"
        "/help — Показать это сообщение",
        parse_mode="Markdown",
    )


@router.message(Command("adhkar"))
async def cmd_adhkar(message: Message):
    await message.answer(
        "📿 *Азкары и дуа*\n\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "cat_morning")
async def cb_morning(callback: CallbackQuery):
    dua = random.choice(MORNING_ADHKAR)
    await callback.message.answer(
        format_dua(dua, "🌅 *Утренний азкар*"),
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "cat_evening")
async def cb_evening(callback: CallbackQuery):
    dua = random.choice(EVENING_ADHKAR)
    await callback.message.answer(
        format_dua(dua, "🌆 *Вечерний азкар*"),
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "cat_after_prayer")
async def cb_after_prayer(callback: CallbackQuery):
    dua = random.choice(AFTER_PRAYER_DUAS)
    await callback.message.answer(
        format_dua(dua, "🕌 *Дуа после намаза*"),
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "cat_random")
async def cb_random(callback: CallbackQuery):
    all_duas = DUAS + MORNING_ADHKAR + EVENING_ADHKAR + AFTER_PRAYER_DUAS
    dua = random.choice(all_duas)
    await callback.message.answer(
        format_dua(dua, "🎲 *Случайная дуа*"),
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, scheduler, bot):
    chat_id = message.chat.id
    already = await is_subscribed(chat_id)
    if already:
        time_str = await get_subscriber_time(chat_id)
        await message.answer(
            f"✅ Ты уже подписан! Ежедневная дуа отправляется в *{time_str} UTC*.\n\n"
            "Используй /settime для смены времени или /dua для дуа прямо сейчас.",
            parse_mode="Markdown",
        )
        return

    await add_subscriber(chat_id)
    await reschedule_user(scheduler, bot, chat_id)
    time_str = await get_subscriber_time(chat_id)

    await message.answer(
        f"✅ *Подписка оформлена!*\n\n"
        f"Ты будешь получать ежедневную дуа в *{time_str} UTC* каждый день. 🌙\n\n"
        "Используй /settime для изменения времени или /dua для дуа прямо сейчас. 🤲",
        parse_mode="Markdown",
    )


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message, scheduler):
    chat_id = message.chat.id
    if not await is_subscribed(chat_id):
        await message.answer(
            "❌ Ты не подписан на ежедневные напоминания.\nИспользуй /subscribe, чтобы начать получать дуа."
        )
        return

    await remove_subscriber(chat_id)
    remove_user_schedule(scheduler, chat_id)
    await message.answer(
        "✅ Ты *отписан* от ежедневных напоминаний.\n\n"
        "Ежедневные дуа больше не будут приходить. Возвращайся в любое время с помощью /subscribe 🤲",
        parse_mode="Markdown",
    )


@router.message(Command("settime"))
async def cmd_settime(message: Message, scheduler, bot):
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        current = await get_subscriber_time(chat_id) if await is_subscribed(chat_id) else "07:00"
        await message.answer(
            f"🕐 *Установка времени напоминания*\n\n"
            f"Текущее время: *{current} UTC*\n\n"
            "Укажи желаемое время в 24-часовом формате:\n"
            "`/settime ЧЧ:ММ`\n\n"
            "Примеры:\n"
            "`/settime 06:00` — 6:00 утра UTC\n"
            "`/settime 20:30` — 20:30 вечера UTC\n\n"
            "⚠️ Всё время указывается в UTC. При необходимости воспользуйся конвертером часовых поясов.",
            parse_mode="Markdown",
        )
        return

    time_str = args[1].strip()
    if not re.match(r"^\d{1,2}:\d{2}$", time_str):
        await message.answer(
            "❌ Неверный формат. Используй формат ЧЧ:ММ, например: `/settime 07:00`",
            parse_mode="Markdown",
        )
        return

    parts = time_str.split(":")
    hour, minute = int(parts[0]), int(parts[1])

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer("❌ Неверное время. Часы должны быть от 0 до 23, минуты — от 0 до 59.")
        return

    time_str = f"{hour:02d}:{minute:02d}"

    if not await is_subscribed(chat_id):
        await add_subscriber(chat_id, time_str)
    else:
        await set_subscriber_time(chat_id, time_str)

    await reschedule_user(scheduler, bot, chat_id)
    await message.answer(
        f"✅ Время напоминания обновлено: *{time_str} UTC*! 🌙\n\n"
        "Подписка активна — ежедневная дуа будет приходить в указанное время.",
        parse_mode="Markdown",
    )


@router.message(Command("dua"))
async def cmd_dua(message: Message):
    dua = random.choice(DUAS)
    await message.answer(
        format_dua(dua),
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    chat_id = message.chat.id
    subscribed = await is_subscribed(chat_id)
    if subscribed:
        time_str = await get_subscriber_time(chat_id)
        await message.answer(
            f"✅ *Подписка активна*\n\n"
            f"Время ежедневного напоминания: *{time_str} UTC*\n\n"
            "Используй /settime для смены времени или /unsubscribe для отписки.",
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "❌ *Подписка не оформлена*\n\n"
            "Используй /subscribe, чтобы начать получать ежедневные дуа.",
            parse_mode="Markdown",
        )


@router.message(Command("users"))
async def cmd_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет доступа к этой команде.")
        return

    subscribers = await get_all_subscribers()
    count = len(subscribers)
    await message.answer(
        f"👥 *Статистика пользователей*\n\n"
        f"Зарегистрировано подписчиков: *{count}*",
        parse_mode="Markdown",
    )
