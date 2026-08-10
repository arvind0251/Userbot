# PhoenixUB

Fresh, from-scratch Telegram userbot — VC music/video streaming (latest PyTgCalls v2 /
NTgCalls), owner/sudo system, global moderation, and utility commands. Uses BabyAPI as
the stream source.

## Features

- **VC Music/Video**: `.play`, `.vply`, `.cplay`, `.cvply`, `.pause`, `.resume`, `.skip`,
  `.stop`, `.mute`, `.unmute` — with a per-chat queue.
- **Owner/Sudo system**: `.addsudo`, `.delsudo`, `.sudolist` — gate all sensitive commands.
- **PM Guard**: warns and eventually blocks strangers who spam the userbot's PMs.
- **Global moderation**: `.gban`, `.ungban`, `.gbanlist`, `.gmute`, `.gunmute` — acts across
  every chat the account is in and stores state in MongoDB, so it persists restarts.
- **Chat tools**: `.del`, `.purge`.
- **Utility**: `.ping`, `.alive`, `.id`, `.help`.

Note: mass-messaging / chat-flooding ("raid") plugins were intentionally left out.

## Setup

```bash
git clone <this-repo-once-you-push-it>
cd PhoenixUB
cp .env.example .env
nano .env          # fill in real values (see below)
pip install -r requirements.txt --break-system-packages
python3 main.py
```

### Required .env values

| Variable | Where to get it |
|---|---|
| `API_ID` / `API_HASH` | https://my.telegram.org |
| `STRING_SESSION` | Generate with Kurigram (`Client(...).export_session_string()`) for the account you want the userbot to run as |
| `OWNER_ID` | Your numeric Telegram user ID (e.g. via @userinfobot) |
| `MONGO_DB_URL` | MongoDB Atlas connection string |
| `API_KEY` | Your BabyAPI key |

### Optional

- `BOT_TOKEN` — a helper bot client, if you want bot-side features later.
- `ASSISTANT_SESSION` — a second account's session string, dedicated to joining VCs so
  your main account isn't tied up in every call.
- `LOG_GROUP_ID` — a group/channel ID to send startup/error logs to.

## Project structure

```
PhoenixUB/
├── main.py                  entry point
├── config.py                env var loading
├── core/
│   ├── clients.py            Pyrogram clients (app / bot / assistant)
│   └── call_manager.py       PyTgCalls instance + queue helpers
├── database/
│   └── mongo.py               sudoers / gban / chats collections
└── modules/
    ├── owner/
    │   ├── sudoers.py         sudo add/del/list + @sudo_only decorator
    │   └── pmguard.py         PM spam warning/block
    ├── vc/
    │   ├── streams.py         BabyAPI fetch logic
    │   ├── play.py            .play/.vply/.cplay/.cvply
    │   └── controls.py        .pause/.resume/.skip/.stop/.mute/.unmute
    ├── global_mod/
    │   ├── gban.py
    │   ├── gmute.py
    │   └── gdel.py             .del/.purge
    └── utils/
        └── basics.py           .ping/.alive/.id/.help
```

## Important: Kurigram, not original Pyrogram

`py-tgcalls` v2.x needs error classes (like `GroupcallForbidden`) that the original,
now largely unmaintained `pyrogram` package doesn't have. This project installs
**Kurigram** instead — an actively maintained fork that's a drop-in replacement
(same `import pyrogram` statements work unchanged). `requirements.txt` already
points to `kurigram`, so a plain `pip install -r requirements.txt` handles this —
just don't `pip install pyrogram` separately, or it will conflict.

## Notes

- Generating `STRING_SESSION` logs into a real personal Telegram account — never share
  this string with anyone, it's equivalent to your account password.
- Never commit `.env` — it's already in `.gitignore`.
- Rotate your BabyAPI key if it's ever been pasted anywhere public.
