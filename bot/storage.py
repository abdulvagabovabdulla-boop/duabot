import json
import os
from typing import Optional

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
    data[str(chat_id)] = {"time": time_str}
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


async def get_all_subscribers() -> list[tuple[int, str]]:
    data = _load()
    return [(int(cid), info.get("time", DEFAULT_TIME)) for cid, info in data.items()]
