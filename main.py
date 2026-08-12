import asyncio
import importlib

from core.clients import app, bot
from database.mongo import add_chat
from modules.owner.sudoers import load_sudoers

# Import every module so its @app.on_message handlers register
MODULES = [
    "modules.owner.sudoers",
    "modules.owner.pmguard",
    "modules.global_mod.gban",
    "modules.global_mod.gmute",
    "modules.global_mod.gdel",
    "modules.global_mod.warn",
    "modules.global_mod.broadcast",
    "modules.global_mod.chatmod",
    "modules.global_mod.tagall",
    "modules.global_mod.shayari",
    "modules.global_mod.bro",
    "modules.owner.clone",
    "modules.public.login",
    "modules.public.start",
    "modules.utils.basics",
    "modules.utils.info",
    "modules.utils.fun",
]
for m in MODULES:
    try:
        importlib.import_module(m)
    except Exception as e:
        print(f"[Bot] WARNING: could not load module '{m}': {type(e).__name__}: {e}")


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
    print("[Bot] Userbot client started.")

    if bot:
        await bot.start()
        print("[Bot] Bot client started.")

    print("[Bot] Bot is ready.")

    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    # NOTE: We intentionally use get_event_loop() + run_until_complete() here
    # instead of asyncio.run(). Pyrogram clients are created at import time
    # (module level in core/clients.py) and grab whatever event loop exists
    # at that moment via get_event_loop(). asyncio.run() always creates a
    # brand-new loop, which would then differ from the one the clients
    # already grabbed -> "attached to a different loop" RuntimeError. Using
    # get_event_loop() here reuses that same loop.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
