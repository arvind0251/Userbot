"""
Fetches playable audio/video files via the ArtistBots API, given a YouTube
search query. Unlike BabyAPI (which returns a JSON stream URL), ArtistBots
directly returns the binary file content on GET, so we download it straight
to a local file and hand PyTgCalls that local path instead of a remote URL.

Search -> video id (youtubesearchpython) -> download binary -> local file path.
"""
import os
import asyncio
import aiohttp
from youtubesearchpython.__future__ import VideosSearch

from config import BASE_URL, API_KEY

DOWNLOAD_DIR = "downloads"
DOWNLOAD_TIMEOUT = 120  # seconds


async def _search_video_id(query: str) -> tuple[str, str, str]:
    """Returns (video_id, title, thumbnail) for the top YouTube search result."""
    search = VideosSearch(query, limit=1)
    result = await search.next()
    if not result["result"]:
        raise ValueError(f"No results found for query: {query}")
    item = result["result"][0]
    vidid = item["id"]
    title = item.get("title", query)
    thumb = ""
    thumbs = item.get("thumbnails") or []
    if thumbs:
        thumb = thumbs[-1]["url"]
    return vidid, title, thumb


async def _download_via_artistbots(vidid: str, want_video: bool) -> str:
    """
    GET {BASE_URL}/download?url=<video_id>&type=audio|video&api_key=<key>
    Streams the binary response straight to a local file, returns the path.
    """
    if not API_KEY:
        raise RuntimeError("[ArtistBots] No API_KEY configured in .env")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_ext = ".mp4" if want_video else ".mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{vidid}{file_ext}")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    endpoint = f"{BASE_URL.rstrip('/')}/download"
    params = {"url": vidid, "type": "video" if want_video else "audio", "api_key": API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            endpoint, params=params, timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
        ) as resp:
            if resp.status != 200:
                body = (await resp.text())[:300]
                raise RuntimeError(f"[ArtistBots] HTTP {resp.status}: {body}")

            with open(file_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(65536):
                    f.write(chunk)

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise RuntimeError("[ArtistBots] Download completed but file is empty")

    return file_path


async def get_result(query: str, video: bool = False) -> dict:
    """
    Main entry point. Returns dict: {title, stream_url, thumbnail, video}
    `stream_url` here is actually a local file path — MediaStream() accepts
    both local paths and remote URLs, so no other code needs to change.
    Raises ValueError/RuntimeError on failure (caller should catch and reply to user).
    """
    vidid, title, thumb = await _search_video_id(query)

    file_path = await _download_via_artistbots(vidid, video)

    print(f"[ArtistBots] Ready: {title} -> {file_path}")
    return {"title": title, "stream_url": file_path, "thumbnail": thumb, "video": video}
