"""
PyTgCalls (v2 / NTgCalls-based) instance + a simple in-memory queue system.
Docs: https://pytgcalls.github.io/
"""
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

from core.clients import call_client

pytgcalls = PyTgCalls(call_client)

# chat_id -> list[dict(title, url, video, requested_by)]
QUEUES: dict[int, list[dict]] = {}
# chat_id -> currently playing track dict
CURRENT: dict[int, dict] = {}


def get_queue(chat_id: int) -> list:
    return QUEUES.setdefault(chat_id, [])


async def play_track(chat_id: int, stream_url: str, video: bool = False):
    """Join / change stream in a chat's VC with the given direct stream URL.

    NOTE: py-tgcalls v2.x's `play()` handles both the initial join AND
    switching an already-active stream — there's no separate
    join_group_call() in this version, so we just call play() once.
    """
    if video:
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.SD_480p,
        )
    else:
        # Don't pass video_parameters at all for audio-only — the library
        # doesn't accept None there, only a real VideoQuality/VideoParameters
        # or omitting the kwarg (which defaults to audio-only + no video).
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.STUDIO,
        )
    await pytgcalls.play(chat_id, stream)


async def stop_stream(chat_id: int):
    QUEUES.pop(chat_id, None)
    CURRENT.pop(chat_id, None)
    try:
        await pytgcalls.leave_call(chat_id)
    except Exception:
        pass


async def pause_stream(chat_id: int):
    await pytgcalls.pause(chat_id)


async def resume_stream(chat_id: int):
    await pytgcalls.resume(chat_id)


async def mute_stream(chat_id: int):
    await pytgcalls.mute(chat_id)


async def unmute_stream(chat_id: int):
    await pytgcalls.unmute(chat_id)
