"""
Shared helper: schedule a bot response message for deletion after a short
delay, without blocking the handler. Used across all command modules so
every command's output auto-cleans itself from the chat.
"""
import asyncio

DEFAULT_DELETE_DELAY = 0.5


def auto_delete(msg, delay: float = DEFAULT_DELETE_DELAY):
    """Fire-and-forget: delete `msg` after `delay` seconds."""
    if msg is None:
        return

    async def _task():
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except Exception:
            pass

    asyncio.create_task(_task())
