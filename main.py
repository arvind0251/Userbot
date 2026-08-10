import asyncio
import importlib

from core.clients import app, bot, assistant
from core.call_manager import pytgcalls
from database.mongo import add_chat
from modules.owner.sudoers import load_sudoers

# Import every module so its @app.on_message handlers register
MODULES = [
    "modules.owner.sudoers",
    "modules.owner.pmguard",
    "modules.vc.play",
    "modules.vc.controls",
    "modules.global_mod.gban",
    "modules.global_mod.gmute",
    "modules.global_mod.gdel",
    "modules.utils.basics",
]
for m in MODULES:
    importlib.import_module(m)


async def track_new_chats():
    """Keep the `chats` collection updated so global mod tools know where to act."""
    from pyrogram import filters

    @app.on_message(filters.group, group=-1)
    async def _track(client, message):
        try:
            await add_chat(message.chat.id, message.chat.title or "")
        except Exception:
            pass


async def main():
    await load_sudoers()
    await track_new_chats()

    await app.start()
    print("[PhoenixUB] Userbot client started.")

    if bot:
        await bot.start()
        print("[PhoenixUB] Bot client started.")

    if assistant:
        await assistant.start()
        print("[PhoenixUB] Assistant client started.")

    await pytgcalls.start()
    print("[PhoenixUB] PyTgCalls started. Bot is ready.")

    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
