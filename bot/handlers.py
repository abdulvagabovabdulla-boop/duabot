import random
import re
import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from duas import DUAS, MORNING_ADHKAR, EVENING_ADHKAR, AFTER_PRAYER_DUAS, get_dua_of_day, search_duas
from storage import (
    add_subscriber,
    remove_subscriber,
    is_subscribed,
    get_subscriber_time,
    set_subscriber_time,
    get_all_subscribers,
    get_stats,
    get_dua_enabled,
    set_dua_enabled,
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
        "/duaofday — ☀️ Дуа дня\n"
        "/duaoff — 🔕 Отключить дуа дня\n"
        "/duaon — 🔔 Включить дуа дня\n"
        "/search — 🔍 Поиск дуа по слову\n"
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
        "/duaofday — ☀️ Дуа дня\n"
        "/duaoff — 🔕 Отключить дуа дня\n"
        "/duaon — 🔔 Включить дуа дня\n"
        "/search — 🔍 Поиск дуа по слову\n"
        "/dua — Получить случайную дуа прямо сейчас\n"
        "/adhkar — Азкары и дуа по категориям\n"
        "/status — Проверить статус подписки\n"
        "/help — Показать это сообщение",
        parse_mode="Markdown",
    )


@router.message(Command("duaoff"))
async def cmd_dua_off(message: Message):
    chat_id = message.chat.id
    if not await is_subscribed(chat_id):
        await message.answer("❌ Сначала подпишись с помощью /subscribe.")
        return
    await set_dua_enabled(chat_id, False)
    await message.answer(
        "🔕 *Дуа дня отключена.*\n\n"
        "Ежедневные напоминания больше не будут приходить.\n"
        "Включить снова — /duaon",
        parse_mode="Markdown",
    )


@router.message(Command("duaon"))
async def cmd_dua_on(message: Message):
    chat_id = message.chat.id
    if not await is_subscribed(chat_id):
        await message.answer("❌ Сначала подпишись с помощью /subscribe.")
        return
    await set_dua_enabled(chat_id, True)
    time_str = await get_subscriber_time(chat_id)
    await message.answer(
        "🔔 *Дуа дня включена!*\n\n"
        f"Каждый день в *{time_str} UTC* будет приходить тихое напоминание с дуа. 🤲\n"
        "Отключить — /duaoff",
        parse_mode="Markdown",
    )


@router.message(Command("duaofday"))
async def cmd_dua_of_day(message: Message):
    from datetime import datetime, timezone
    dua = get_dua_of_day()
    date_str = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    text = (
        f"☀️ *Дуа дня — {date_str}*\n\n"
        f"*{dua['title']}*\n\n"
        f"{dua['arabic']}\n\n"
        f"*Транслитерация:*\n_{dua['transliteration']}_\n\n"
        f"*Перевод:*\n{dua['translation']}\n\n"
        f"📖 {dua['source']}"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("adhkar"))
async def cmd_adhkar(message: Message):
    await message.answer(
        "📿 *Азкары и дуа*\n\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "cat_morning")
async def cb_morning(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        f"🌅 *Утренние азкары*\n\nЧитаются после намаза фаджр (утреннего намаза). Всего {len(MORNING_ADHKAR)} азкаров:",
        parse_mode="Markdown",
    )
    for i, dua in enumerate(MORNING_ADHKAR, 1):
        text = (
            f"🌅 *{i}/{len(MORNING_ADHKAR)} — {dua['title']}*\n\n"
            f"{dua['arabic']}\n\n"
            f"*Транслитерация:*\n_{dua['transliteration']}_\n\n"
            f"*Перевод:*\n{dua['translation']}\n\n"
            f"📖 {dua['source']}"
        )
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.message.answer("✅ Все утренние азкары прочитаны. Джазакумуллаху хайран! 🤲", reply_markup=main_menu())


@router.callback_query(F.data == "cat_evening")
async def cb_evening(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        f"🌆 *Вечерние азкары*\n\nЧитаются после намаза аср или магриб. Всего {len(EVENING_ADHKAR)} азкаров:",
        parse_mode="Markdown",
    )
    for i, dua in enumerate(EVENING_ADHKAR, 1):
        text = (
            f"🌆 *{i}/{len(EVENING_ADHKAR)} — {dua['title']}*\n\n"
            f"{dua['arabic']}\n\n"
            f"*Транслитерация:*\n_{dua['transliteration']}_\n\n"
            f"*Перевод:*\n{dua['translation']}\n\n"
            f"📖 {dua['source']}"
        )
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.message.answer("✅ Все вечерние азкары прочитаны. Джазакумуллаху хайран! 🤲", reply_markup=main_menu())


@router.callback_query(F.data == "cat_after_prayer")
async def cb_after_prayer(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        f"🕌 *Дуа после намаза*\n\nЧитаются сразу после завершения каждого намаза. Всего {len(AFTER_PRAYER_DUAS)} дуа:",
        parse_mode="Markdown",
    )
    for i, dua in enumerate(AFTER_PRAYER_DUAS, 1):
        text = (
            f"🕌 *{i}/{len(AFTER_PRAYER_DUAS)} — {dua['title']}*\n\n"
            f"{dua['arabic']}\n\n"
            f"*Транслитерация:*\n_{dua['transliteration']}_\n\n"
            f"*Перевод:*\n{dua['translation']}\n\n"
            f"📖 {dua['source']}"
        )
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.message.answer("✅ Все дуа после намаза. Да примет Аллах ваш намаз! 🤲", reply_markup=main_menu())


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


@router.message(Command("search"))
async def cmd_search(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer(
            "🔍 *Поиск дуа*\n\n"
            "Напиши слово после команды:\n"
            "`/search никах`\n"
            "`/search здоровье`\n"
            "`/search сон`\n"
            "`/search экзамен`\n"
            "`/search еда`\n"
            "`/search защита`",
            parse_mode="Markdown",
        )
        return

    query = args[1].strip()
    results = search_duas(query)

    if not results:
        await message.answer(
            f"😔 По запросу *«{query}»* ничего не найдено.\n\n"
            "Попробуй другое слово, например:\n"
            "`/search сон` · `/search здоровье` · `/search никах`\n"
            "`/search еда` · `/search экзамен` · `/search защита`",
            parse_mode="Markdown",
        )
        return

    await message.answer(
        f"🔍 По запросу *«{query}»* найдено *{len(results)}* дуа:",
        parse_mode="Markdown",
    )
    for dua in results[:5]:
        text = (
            f"*{dua['title']}*\n\n"
            f"{dua['arabic']}\n\n"
            f"*Транслитерация:*\n_{dua['transliteration']}_\n\n"
            f"*Перевод:*\n{dua['translation']}\n\n"
            f"📖 {dua['source']}"
        )
        await message.answer(text, parse_mode="Markdown")

    if len(results) > 5:
        await message.answer(
            f"_Показаны первые 5 из {len(results)}. Уточни запрос для более точного результата._",
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

    stats = await get_stats()
    total = stats["total"]
    today = stats["today"]
    yesterday = stats["yesterday"]
    week = stats["week"]

    today_pct = round(today / total * 100, 1) if total else 0
    yesterday_pct = round(yesterday / total * 100, 1) if total else 0
    week_pct = round(week / total * 100, 1) if total else 0

    def bar(pct: float) -> str:
        filled = round(pct / 10)
        return "█" * filled + "░" * (10 - filled) + f" {pct}%"

    await message.answer(
        f"👥 *Статистика подписчиков*\n\n"
        f"📊 Всего: *{total}* чел.\n\n"
        f"📅 Сегодня: *+{today}*\n"
        f"`{bar(today_pct)}`\n\n"
        f"📅 Вчера: *+{yesterday}*\n"
        f"`{bar(yesterday_pct)}`\n\n"
        f"📅 За 7 дней: *+{week}*\n"
        f"`{bar(week_pct)}`",
        parse_mode="Markdown",
    )
