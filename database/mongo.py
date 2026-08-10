from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URL

_client = AsyncIOMotorClient(MONGO_DB_URL) if MONGO_DB_URL else None
_db = _client["PhoenixUB"] if _client else None

sudoers_col = _db["sudoers"] if _db is not None else None
gban_col = _db["gbans"] if _db is not None else None
chats_col = _db["chats"] if _db is not None else None


# ===================== Sudo users =====================
async def add_sudo(user_id: int):
    await sudoers_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)


async def remove_sudo(user_id: int):
    await sudoers_col.delete_one({"user_id": user_id})


async def get_sudoers() -> list[int]:
    cursor = sudoers_col.find({})
    return [doc["user_id"] async for doc in cursor]


# ===================== Global ban =====================
async def gban_user(user_id: int, reason: str = "No reason given"):
    await gban_col.update_one(
        {"user_id": user_id}, {"$set": {"user_id": user_id, "reason": reason}}, upsert=True
    )


async def ungban_user(user_id: int):
    await gban_col.delete_one({"user_id": user_id})


async def is_gbanned(user_id: int) -> bool:
    doc = await gban_col.find_one({"user_id": user_id})
    return doc is not None


async def get_gban_list() -> list[dict]:
    cursor = gban_col.find({})
    return [doc async for doc in cursor]


# ===================== Chats the bot is active in =====================
async def add_chat(chat_id: int, title: str = ""):
    await chats_col.update_one(
        {"chat_id": chat_id}, {"$set": {"chat_id": chat_id, "title": title}}, upsert=True
    )


async def remove_chat(chat_id: int):
    await chats_col.delete_one({"chat_id": chat_id})


async def get_all_chats() -> list[int]:
    cursor = chats_col.find({})
    return [doc["chat_id"] async for doc in cursor]
