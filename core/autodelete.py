"""
Auto-deletes the INCOMING command message the user typed (e.g. ".rose"),
after a short delay — the bot's response/output is left alone and stays
in the chat. Registered once, globally, for the main userbot client, so
no individual command module needs to handle this itself.
"""
import asyncio
from pyrogram import filters
from pyrogram.types import Message

DELETE_DELAY = 0.5


def register_trigger_autodelete(app):
    @app.on_message(filters.text & filters.regex(r"^[.!]\w"), group=-20)
    async def _delete_trigger(client, message: Message):
        async def _task():
            await asyncio.sleep(DELETE_DELAY)
            try:
                await message.delete()
            except Exception:
                pass
        asyncio.create_task(_task())
        message.continue_propagation()
