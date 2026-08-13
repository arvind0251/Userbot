"""
Gives a clone/login Client the FULL command set — every handler currently
registered on the main userbot (`app`) gets copied onto the new client.

This works because Pyrogram handler callbacks are plain functions of
(client, message) — they aren't bound to a specific Client instance — so
the exact same handler objects can be attached to multiple clients safely.
Since @sudo_only checks the sender's user ID against the global sudo list
(not which client dispatched the message), and only owner/sudo can create
a clone/login in the first place, this is safe: whoever owns the clone
already has sudo rights on the main bot too.

Because this copies whatever is registered on `app` at call time rather
than a hardcoded list, any new command added to the bot automatically
becomes available on clones too, with no changes needed here.
"""
from pyrogram import Client

from core.clients import app


async def clone_all_handlers(target_client: Client):
    for group, handlers in app.dispatcher.groups.items():
        for handler in handlers:
            target_client.add_handler(handler, group)


# Kept for backward compatibility with any old imports.
register_common_handlers = clone_all_handlers
