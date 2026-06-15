import json
import os
from datetime import datetime, timezone, timedelta

STORAGE_FILE = os.path.join(os.path.dirname(__file__), "subscribers.json")
DEFAULT_TIME = "07:00"


def _load() -> dict:
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data: dict):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def add_subscriber(chat_id: int, time_str: str = DEFAULT_TIME):
    data = _load()
    if str(chat_id) not in data:
        data[str(chat_id)] = {
            "time": time_str,
            "joined_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "dua_enabled": True,
        }
    else:
        data[str(chat_id)]["time"] = time_str
        if "dua_enabled" not in data[str(chat_id)]:
            data[str(chat_id)]["dua_enabled"] = True
    _save(data)


async def remove_subscriber(chat_id: int):
    data = _load()
    data.pop(str(chat_id), None)
    _save(data)


async def is_subscribed(chat_id: int) -> bool:
    data = _load()
    return str(chat_id) in data


async def get_subscriber_time(chat_id: int) -> str:
    data = _load()
    entry = data.get(str(chat_id), {})
    return entry.get("time", DEFAULT_TIME)


async def set_subscriber_time(chat_id: int, time_str: str):
    data = _load()
    if str(chat_id) not in data:
        data[str(chat_id)] = {}
    data[str(chat_id)]["time"] = time_str
    _save(data)


async def get_dua_enabled(chat_id: int) -> bool:
    data = _load()
    entry = data.get(str(chat_id), {})
    return entry.get("dua_enabled", True)


async def set_dua_enabled(chat_id: int, enabled: bool):
    data = _load()
    if str(chat_id) not in data:
        data[str(chat_id)] = {}
    data[str(chat_id)]["dua_enabled"] = enabled
    _save(data)


async def get_all_subscribers() -> list[tuple[int, str]]:
    data = _load()
    return [(int(cid), info.get("time", DEFAULT_TIME)) for cid, info in data.items()]


async def get_stats() -> dict:
    data = _load()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    total = len(data)
    joined_today = sum(1 for info in data.values() if info.get("joined_at") == today)
    joined_yesterday = sum(1 for info in data.values() if info.get("joined_at") == yesterday)

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    joined_week = sum(
        1 for info in data.values()
        if info.get("joined_at", "0000-00-00") >= week_ago
    )

    return {
        "total": total,
        "today": joined_today,
        "yesterday": joined_yesterday,
        "week": joined_week,
    }
