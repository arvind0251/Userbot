"""
Per-client PyTgCalls management — every account has its OWN VC engine.

Previously there was a single global PyTgCalls instance bound to one
client (assistant or app), so music from a clone/login'd account actually
played through the ORIGINAL account's voice-chat connection. Now each
client (main app, or any account added via .login/.clone) gets its own
PyTgCalls instance, lazily created and started on first use, so every
logged-in account can independently join/play in voice chats.

Special case: the main `app` client still delegates to `assistant` (if
configured via ASSISTANT_SESSION) to avoid tying up the main account —
this matches the original design. Any OTHER client (a clone or a
.login'd account) always uses itself, since that's the whole point of
that account being logged in separately.
"""
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

from core.clients import app, assistant

# id(client) -> PyTgCalls instance
_INSTANCES: dict[int, PyTgCalls] = {}
# id(client) -> bool, whether .start() has been called on that instance
_STARTED: dict[int, bool] = {}

# id(client) -> {chat_id: [queued track dicts]}
_QUEUES: dict[int, dict[int, list[dict]]] = {}
# id(client) -> {chat_id: currently playing track dict}
_CURRENT: dict[int, dict[int, dict]] = {}


def _resolve_call_client(client):
    """Which underlying Pyrogram client actually joins the VC for this
    handler's `client`. Only the main `app` delegates to `assistant`."""
    if client is app and assistant is not None:
        return assistant
    return client


def get_pytgcalls(client) -> PyTgCalls:
    call_client = _resolve_call_client(client)
    key = id(call_client)
    if key not in _INSTANCES:
        _INSTANCES[key] = PyTgCalls(call_client)
    return _INSTANCES[key]


async def ensure_started(client):
    """Starts this client's PyTgCalls instance once, lazily on first use."""
    call_client = _resolve_call_client(client)
    key = id(call_client)
    if not _STARTED.get(key):
        await get_pytgcalls(client).start()
        _STARTED[key] = True


def get_queue(client, chat_id: int) -> list:
    key = id(_resolve_call_client(client))
    return _QUEUES.setdefault(key, {}).setdefault(chat_id, [])


def get_current(client) -> dict:
    key = id(_resolve_call_client(client))
    return _CURRENT.setdefault(key, {})


async def play_track(client, chat_id: int, stream_url: str, video: bool = False):
    """Join / change stream in a chat's VC with the given URL or local file path."""
    await ensure_started(client)
    pytgcalls = get_pytgcalls(client)

    if video:
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.SD_480p,
        )
    else:
        # Don't pass video_parameters at all for audio-only — the library
        # doesn't accept None there, only a real VideoQuality/VideoParameters
        # or video_flags=IGNORE.
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.STUDIO,
            video_flags=MediaStream.Flags.IGNORE,
        )
    await pytgcalls.play(chat_id, stream)


async def stop_stream(client, chat_id: int):
    key = id(_resolve_call_client(client))
    _QUEUES.get(key, {}).pop(chat_id, None)
    _CURRENT.get(key, {}).pop(chat_id, None)
    try:
        await get_pytgcalls(client).leave_call(chat_id)
    except Exception:
        pass


async def pause_stream(client, chat_id: int):
    await get_pytgcalls(client).pause(chat_id)


async def resume_stream(client, chat_id: int):
    await get_pytgcalls(client).resume(chat_id)


async def mute_stream(client, chat_id: int):
    await get_pytgcalls(client).mute(chat_id)


async def unmute_stream(client, chat_id: int):
    await get_pytgcalls(client).unmute(chat_id)
