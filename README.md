# Userbot

Telegram userbot — moderation, self-service account cloning, and fun extras.
All commands are restricted to the owner and sudo users, except the
self-service `.login`/`.clone` flow, which is intentionally open to anyone
(PM-only, for safety).

## Features

- **Music/VC**: `.play`, `.vply`, `.cplay`, `.cvply` — play audio/video in a group's voice
  chat, with a per-chat queue. `.pause`/`.resume`/`.skip`/`.stop`, `.vmute`/`.vunmute`.
  Uses [Kurigram](https://github.com/KurimuzonAkuma/pyrogram) + PyTgCalls v2 for the VC
  connection and BabyAPI (`BASE_URL`/`API_KEY`) as the stream source. An optional
  `ASSISTANT_SESSION` account can join VCs instead of tying up the main account.
  **Every account gets its own independent VC engine** — this includes any account
  added via `.clone`/`.login` (see below), so multiple logged-in accounts can each
  play music through their own identity at the same time, not just the main account.
- **Owner/Sudo system**: `.addsudo`, `.delsudo`, `.sudolist` — gate all sensitive commands.
- **PM Guard**: warns and eventually blocks strangers who spam the userbot's PMs.
  `.approve` / `.unapprove` / `.approved` let sudo users exempt specific people from
  these warnings entirely.
- **Global moderation**: `.gban`, `.ungban`, `.gbanlist`, `.gmute`, `.gunmute` — acts across
  every chat the account is in and stores state in a local `storage.json` file, so it
  persists restarts (no external database needed).
- **This-chat moderation**: `.ban`, `.unban`, `.kick`, `.mute`, `.unmute` for single users,
  plus `.banall`/`.kickall`/`.muteall`/`.unmuteall` for every non-admin in the current chat.
- **Warn system**: `.warn`, `.unwarn`, `.warns`, `.resetwarns` — auto-bans a user after 3
  warns in the same chat (configurable via `MAX_WARNS` in `modules/global_mod/warn.py`).
- **Broadcast**: `.broadcast <text>` (or reply to any message with `.broadcast`) sends it
  to every chat the account is currently in.
- **Tag all**: `.tagall [message]` — mentions every non-bot member in small batches (5 at
  a time, with a short delay) to stay under Telegram's flood limits; `.tagallstop`
  interrupts it partway through (handy for large groups where it takes a while); `.tagme`
  mentions just yourself.
- **Shayari / Love**: `.sha` and `.love` each work three ways — reply to someone for a
  one-off message tagging just them; use with no reply to tag the whole group once;
  or `.sha 20` / `.love 20` to start a recurring broadcast every 20 minutes (10-minute
  minimum), stopped with `.sha stop` / `.love stop`. 100 unique lines each, all original
  (not copied from any song or published poem) to stay clear of copyright.
- **Casual `.bro`**: one-shot, manually-triggered casual/flirty text — sends directly in
  DM, or in a group only when replying to someone (so it's always aimed at one specific
  person you chose, never automated or looped).
- **Fun animations**: `.cat`, `.rose`, `.hacker`, `.error`, `.butterfly`, `.myson`,
  `.heart` — cosmetic ASCII-art/emoji animations.
- **Welcome messages**: `.welcome on`/`.welcome off` toggles a per-chat welcome message
  for new members (off by default); `.setwelcome <text>` customizes it with `{name}`,
  `{mention}`, `{chat}`, `{id}` placeholders.
- **Cloning**: `.clone <bot_token>` (owner/sudo only) spins up a separate bot that gets
  the **full command set** — every handler currently registered on the main userbot is
  copied onto the clone automatically, so new commands added later work on clones too
  with no extra changes needed. `.unclone`/`.clonelist` manage running clones.
- **Owner/sudo login system**: `.login` — runs through **the bot account (`BOT_TOKEN`),
  not the userbot** — so this flow never touches the main personal account. Restricted
  to owner/sudo (via `@sudo_only`), same as everything else. The resulting clone also
  gets the full command set. Two ways to use it:
  - `.login` (no args) — guided flow: bot asks for your phone number, sends you a
    Telegram login code, you reply with the code (and 2FA password if you have one),
    and it logs you in automatically, then hands you the resulting session string.
  - `.login <string_session>` — paste an existing session string directly, if you
    already generated one yourself.
  `.logout` / `.mylogin` / `.cancellogin` manage sessions. **Multiple sessions can be
  active at once** — running `.login` again with a different account adds it alongside
  any existing ones (each with its own full command set and independent VC engine, so
  they can all play music simultaneously); logging into the SAME account again just
  refreshes that one entry. `.mylogin` lists all active sessions; `.logout <account_id>`
  or `.logout all` manage them. Each resulting session string is equivalent to full
  account access.

## Setup

```bash
git clone <this-repo>
cd userbot
cp .env.example .env
nano .env          # fill in real values (see below)
pip install -r requirements.txt
python3 main.py
```

### Required .env values

| Variable | Where to get it |
|---|---|
| `API_ID` / `API_HASH` | https://my.telegram.org |
| `STRING_SESSION` | Generate with Kurigram (`Client(...).export_session_string()`) for the account you want the userbot to run as |
| `OWNER_ID` | Your numeric Telegram user ID (e.g. via @userinfobot) |
| `API_KEY` | Your BabyAPI key (needed for `.play`/`.vply` to actually fetch audio/video) |

### Optional

- `BOT_TOKEN` — a helper bot account that runs the self-service `.login`/`.clone` flow.
  Required if you want that feature at all.
- `ASSISTANT_SESSION` — a second account's session string, dedicated to joining VCs so
  your main account isn't tied up in every call. Falls back to the main account if unset.
- `BASE_URL` — BabyAPI base URL, defaults to `https://api.babiesiq.tech`.
- `LOG_GROUP_ID` — a group/channel ID to send startup/error logs to.

## Project structure

```
userbot/
├── main.py                  entry point
├── config.py                env var loading
├── core/
│   ├── clients.py             Pyrogram clients (app / bot / assistant)
│   ├── call_manager.py        per-client PyTgCalls instances + queue helpers
│   └── clone_handlers.py      copies app's full handler set onto clone/login clients
├── database/
│   └── mongo.py               sudoers / gban / warns / chats / approved — local storage.json file
└── modules/
    ├── vc/
    │   ├── streams.py           BabyAPI fetch logic
    │   ├── play.py               .play/.vply/.cplay/.cvply
    │   └── controls.py           .pause/.resume/.skip/.stop/.vmute/.vunmute
    ├── owner/
    │   ├── sudoers.py         sudo add/del/list + @sudo_only decorator
    │   ├── pmguard.py         PM spam warning/block + approve system
    │   └── clone.py            .clone/.unclone/.clonelist (sudo-only)
    ├── public/
    │   ├── login.py            .login/.logout/.mylogin (open to everyone, PM-only)
    │   └── start.py            /start welcome message for the bot account
    ├── global_mod/
    │   ├── gban.py
    │   ├── gmute.py
    │   ├── gdel.py             .del/.purge
    │   ├── chatmod.py          .ban/.kick/.mute (+all variants)
    │   ├── warn.py             .warn/.unwarn/.warns/.resetwarns
    │   ├── broadcast.py         .broadcast
    │   ├── tagall.py            .tagall/.tagallstop/.tagme
    │   ├── shayari.py           .sha/.love
    │   └── bro.py               .bro
    └── utils/
        ├── basics.py           .ping/.alive/.id/.help
        ├── info.py             .info
        └── fun.py               .cat/.rose/.hacker/.error/.butterfly/.myson/.heart
```

## Important: Kurigram, not original Pyrogram

This project uses **Kurigram** — an actively maintained fork of Pyrogram that's a
drop-in replacement (same `import pyrogram` statements work unchanged).
`requirements.txt` already points to `kurigram`, so a plain `pip install -r
requirements.txt` handles this — just don't `pip install pyrogram` separately, or it
will conflict.

## Notes

- Generating `STRING_SESSION` logs into a real personal Telegram account — never share
  this string with anyone, it's equivalent to your account password.
- Never commit `.env` — it's already in `.gitignore`.
