"""
Fetches playable direct stream URLs via BabyAPI, given a YouTube search query.
Search -> video id (youtubesearchpython) -> BabyAPI fetch -> poll until ready.
"""
import asyncio
import time
import requests
from youtubesearchpython.__future__ import VideosSearch

from config import BASE_URL, API_KEY


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


def _baby_fetch_sync(vidid: str, want_video: bool) -> str:
    kind = "video" if want_video else "song"
    url = f"{BASE_URL}/api/{kind}"
    params = {"query": vidid, "download": "true", "api": API_KEY}
    resp = requests.get(url, params=params, timeout=30)
    if not resp.ok:
        # Surface the actual response body (BabyAPI usually explains *why*
        # in the body — invalid/expired key, rate limit, IP block, etc.)
        # since resp.raise_for_status() alone only gives the status code.
        body = resp.text[:300]
        raise RuntimeError(f"[BabyAPI] HTTP {resp.status_code}: {body}")
    data = resp.json()
    stream_url = data.get("stream") or data.get("url") or data.get("stream_url")
    if not stream_url:
        raise ValueError(f"[BabyAPI] No stream url in response: {data}")
    return stream_url


def _wait_until_ready_sync(stream_url: str, timeout: int = 90) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            # Some APIs reject HEAD requests, so use a ranged GET instead —
            # pull just the first byte to confirm the stream is playable
            # without downloading the whole file.
            headers = {"Range": "bytes=0-1"}
            r = requests.get(stream_url, headers=headers, timeout=15, stream=True)
            # Some CDNs (e.g. this one, behind Cloudflare/Railway) return 204
            # No Content for a ranged probe once the stream is ready, instead
            # of 200/206 — treat that as "ready" too.
            if r.status_code in (200, 206, 204):
                r.close()
                return True
            r.close()
        except Exception:
            pass
        time.sleep(3)
    return False


async def get_result(query: str, video: bool = False) -> dict:
    """
    Main entry point. Returns dict: {title, stream_url, thumbnail, video}
    Raises ValueError/RuntimeError on failure (caller should catch and reply to user).
    """
    vidid, title, thumb = await _search_video_id(query)

    loop = asyncio.get_event_loop()
    stream_url = await loop.run_in_executor(None, _baby_fetch_sync, vidid, video)

    ready = await loop.run_in_executor(None, _wait_until_ready_sync, stream_url)
    if not ready:
        raise RuntimeError("[BabyAPI] Stream did not become ready in time, try again.")

    print(f"[BabyAPI] Ready: {title} -> {stream_url}")
    return {"title": title, "stream_url": stream_url, "thumbnail": thumb, "video": video}
