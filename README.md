# PhoenixUB

Fresh, from-scratch Telegram userbot — VC music/video streaming (latest PyTgCalls v2 /
NTgCalls), owner/sudo system, global moderation, and utility commands. Uses BabyAPI as
the stream source.

## Features

- **VC Music/Video**: `.play`, `.vply`, `.cplay`, `.cvply`, `.pause`, `.resume`, `.skip`,
  `.stop`, `.mute`, `.unmute` — with a per-chat queue.
- **Owner/Sudo system**: `.addsudo`, `.delsudo`, `.sudolist` — gate all sensitive commands.
- **PM Guard**: warns and eventually blocks strangers who spam the userbot's PMs.
  `.approve` / `.unapprove` / `.approved` let sudo users exempt specific people from
  these warnings entirely.
- **Global moderation**: `.gban`, `.ungban`, `.gbanlist`, `.gmute`, `.gunmute` — acts across
  every chat the account is in and stores state in a local `storage.json` file, so it
  persists restarts (no external database needed).
- **Warn system**: `.warn`, `.unwarn`, `.warns`, `.resetwarns` — auto-bans a user after 3
  warns in the same chat (configurable via `MAX_WARNS` in `modules/global_mod/warn.py`).
- **Broadcast**: `.broadcast <text>` (or reply to any message with `.broadcast`) sends it
  to every chat the account is currently in.
- **Shayari / Love broadcasts**: `.sha`/`.love` (reply to someone) send a single original
  message tagging them. `.shastart [minutes]`/`.shastop` and `.lovestart [minutes]`/
  `.lovestop` run a recurring broadcast in the chat (minimum 10-minute interval) that
  tags a batch of members each time — meant for your own community, not for repeatedly
  targeting one person. All lines are original, not copied from any song or published
  poem, to stay clear of copyright.
- **Info**: `.info` — shows a user's ID, username, DC ID, premium status, chat role, and
  warn count.
- **This-chat moderation**: `.ban`, `.unban`, `.kick`, `.mute`, `.unmute` for single users,
  plus `.banall`/`.kickall`/`.muteall`/`.unmuteall` for every non-admin in the current chat.
- **Tag all**: `.tagall [message]` — mentions every non-bot member in small batches (5 at
  a time, with a short delay) to stay under Telegram's flood limits; `.tagme` mentions
  just yourself.
- **Cloning**: `.clone <bot_token>` (owner/sudo only) spins up a separate bot that reuses
  this account's VC engine for music commands — good for giving someone their own branded
  bot without a second userbot login. `.unclone`/`.clonelist` manage running clones.
- **Open self-service login**: `.login` — works for **anyone**, PM-only for security,
  and runs through **the bot account (`BOT_TOKEN`), not the userbot** — so this flow
  never touches the main personal account. Two ways to use it:
  - `.login` (no args) — guided flow: bot asks for your phone number, sends you a
    Telegram login code, you reply with the code (and 2FA password if you have one),
    and it logs you in automatically, then hands you the resulting session string.
  - `.login <string_session>` — paste an existing session string directly, if you
    already generated one yourself.
  Either way it starts a personal clone tied to your account, sharing this server's VC
  engine. `.logout` / `.mylogin` / `.cancellogin` manage your own login. One active login
  per person; the resulting session string is equivalent to full account access, so this
  should only be offered to people who trust whoever operates the server.
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
│   ├── call_manager.py       PyTgCalls instance + queue helpers
│   └── clone_handlers.py     shared command-set for clone/login clients
├── database/
│   └── mongo.py               sudoers / gban / chats — local storage.json file
└── modules/
    ├── owner/
    │   ├── sudoers.py         sudo add/del/list + @sudo_only decorator
    │   ├── pmguard.py         PM spam warning/block
    │   └── clone.py            .clone/.unclone/.clonelist (sudo-only)
    ├── public/
    │   └── login.py            .login/.logout/.mylogin (open to everyone, PM-only)
    ├── vc/
    │   ├── streams.py         BabyAPI fetch logic
    │   ├── play.py            .play/.vply/.cplay/.cvply
    │   └── controls.py        .pause/.resume/.skip/.stop/.mute/.unmute
    ├── global_mod/
    │   ├── gban.py
    │   ├── gmute.py
    │   ├── gdel.py             .del/.purge
    │   ├── warn.py             .warn/.unwarn/.warns/.resetwarns
    │   └── broadcast.py         .broadcast
    └── utils/
        ├── basics.py           .ping/.alive/.id/.help
        └── info.py             .info
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
