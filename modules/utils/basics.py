import time
from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from config import BOT_NAME, BOT_USERNAME
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES)


@app.on_message(cmd("ping"))
@sudo_only
async def ping_cmd(client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Pinging...")
    ms = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 Pong! `{ms:.2f}ms`")


@app.on_message(cmd(["alive", "start"]))
@sudo_only
async def alive_cmd(client, message: Message):
    await message.reply_text(
        f"✨ <b>{BOT_NAME}</b> is alive and running.\n"
        f"Use <code>.help</code> to see available commands."
    )


@app.on_message(cmd("id"))
@sudo_only
async def id_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else (
        message.from_user.id if message.from_user else "N/A"
    )
    await message.reply_text(f"Chat ID: <code>{chat_id}</code>\nUser ID: <code>{user_id}</code>")


# ===================== Help: index + detailed per-category pages =====================

HELP_INDEX = f"""
◆━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◆
      ✨ <b>{BOT_NAME}</b> — COMMAND LIST
◆━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     👑 <b>MALIK KE HUKUM — OWNER</b>
◆━━━━━━━━━━━━━━━◆
  🌟.addsudo → Sudo user banao
  🗑️.delsudo → Sudo hatao
  📜.sudolist → Sudo list dekho

  ✅.approve → PM Guard se chhoot
  ❌.unapprove → Chhoot hatao
  📋.approved → Approved list

  👥.clone → Bot token se clone
  🚫.unclone → Clone hatao
  📚.clonelist → Clone list
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
  🔑 <b>SELF LOGIN</b> — {'@' + BOT_USERNAME if BOT_USERNAME else 'the bot'}
◆━━━━━━━━━━━━━━━◆
  📱.login → Phone + OTP guided
  🔢.login &lt;session&gt; → Direct paste
  🚫.cancellogin → Login cancel
  👋.logout → Logout
  ℹ️.mylogin → Login info
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     🌐 <b>GLOBAL DANDA — GLOBAL MOD</b>
◆━━━━━━━━━━━━━━━◆
  🔨.gban → Har jagah Ban
  🕊️.ungban → Global Unban
  📜.gbanlist → GBan List
  🔇.gmute → Har jagah Mute
  🔊.gunmute → Global Unmute
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     👮 <b>CHAT KA RAJA — CHAT MOD</b>
◆━━━━━━━━━━━━━━━◆
  🔨.ban 🕊️.unban 👢.kick
  🔇.mute 🔊.unmute
  💥.banall 💥.kickall 💥.muteall 💥.unmuteall
    → Non-Admins only
  📢.tagall [msg] → Sabko tag karo
  🛑.tagallstop → Tagall band
  🙋.tagme → Khud ko tag
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     ⚠️ <b>WARN SYSTEM</b>
◆━━━━━━━━━━━━━━━◆
  ⚠️.warn → Warning do
  ✅.unwarn → Warning hatao
  📊.warns → Kitni warning hai
  🔄.resetwarns → Warning reset
    - 3 Warn = Seedha Auto Ban 😈
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     📢 <b>BROADCAST</b>
◆━━━━━━━━━━━━━━━◆
  📣.broadcast → Text ya reply karke sabko bhejo
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     📜 <b>SHAYARI / LOVE</b>
◆━━━━━━━━━━━━━━━◆
  🌹.sha → Reply na ho to poore group ko
  💌.sha (reply) → Kisi ek ko tag karke
  ⏰.sha 20 → Har 20 min auto (10 min min)
  🛑.sha stop → Auto band
  ❤️.love → Same, love wali lines
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     👋 <b>MASTI / FUN</b>
◆━━━━━━━━━━━━━━━◆
  😎.bro → Casual (DM / reply)
  🐱.cat 🌹.rose 💖.heart
  💻.hacker ❌.error
  🦋.butterfly 👶.myson
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     🧹 <b>CHAT TOOLS</b>
◆━━━━━━━━━━━━━━━◆
  🗑️.del → Reply msg delete
  🧹.purge → Range delete
◆━━━━━━━━━━━━━━━◆

◆━━━━━━━━━━━━━━━◆
     ⚙️ <b>UTILITY</b>
◆━━━━━━━━━━━━━━━◆
  ⚡.ping ✅.alive 🆔.id
  ℹ️.info 📖.help
◆━━━━━━━━━━━━━━━◆

Type <code>.help &lt;category&gt;</code> (owner/login/global/mod/warn/broadcast/sha/bro/chat/fun/utility) for full usage + examples.
"""

HELP_PAGES = {
    "owner": """
👑 <b>Owner Commands</b>
━━━━━━━━━━━━━━━━━━━━

<code>.addsudo &lt;id&gt;</code>
Reply to a user, or give their numeric ID, to make them a sudo user.
Owner-only. Example: <code>.addsudo 123456789</code>

<code>.delsudo &lt;id&gt;</code>
Same as above, but removes sudo status. Owner-only.

<code>.sudolist</code>
Shows everyone currently in the sudo list.

<code>.approve &lt;id&gt;</code>
Reply to a user, or give their ID, to exempt them from PM Guard warnings
(so they can message this account freely).

<code>.unapprove &lt;id&gt;</code>
Removes that exemption.

<code>.approved</code>
Lists everyone currently PM-approved.

<code>.clone &lt;bot_token&gt;</code>
Starts a separate bot using a token from @BotFather, sharing this
account's basic utility commands. Do this in PM — the token is sensitive.
Example: <code>.clone 123456:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</code>

<code>.unclone &lt;bot_token&gt;</code>
Stops a running clone (same token you started it with).

<code>.clonelist</code>
Shows all currently running clones.
""",

    "login": f"""
🔑 <b>Login System</b>
━━━━━━━━━━━━━━━━━━━━
Owner/sudo only, and only in PM with the bot account
({'@' + BOT_USERNAME if BOT_USERNAME else 'the bot'}) — never the userbot itself.

<code>.login</code>
No arguments: starts a guided flow. The bot asks for your phone number,
sends you a Telegram login code, you reply with the code (and your 2FA
password if you have one), and it logs you in automatically.

<code>.login &lt;session_string&gt;</code>
Already have a Pyrogram/Kurigram session string? Paste it directly to
skip the guided flow.

<code>.cancellogin</code>
Aborts an in-progress login (phone/code/password step).

<code>.logout</code>
Stops your currently active login.

<code>.mylogin</code>
Shows whether you have an active login right now.
""",

    "global": """
🌐 <b>Global Moderation</b>
━━━━━━━━━━━━━━━━━━━━
These act across every chat the account is in (tracked automatically).

<code>.gban &lt;id&gt; [reason]</code>
Reply to a user, or give their ID + optional reason, to ban them
everywhere at once. Example: <code>.gban 123456789 spamming</code>

<code>.ungban &lt;id&gt;</code>
Removes a global ban everywhere.

<code>.gbanlist</code>
Shows everyone currently globally banned, with reasons.

<code>.gmute &lt;id&gt;</code>
Reply to a user, or give their ID, to mute them in every chat.

<code>.gunmute &lt;id&gt;</code>
Removes a global mute everywhere.
""",

    "mod": """
👮 <b>This-Chat Moderation</b>
━━━━━━━━━━━━━━━━━━━━
These only affect the chat you run them in.

<code>.ban &lt;id&gt; [reason]</code> · <code>.unban &lt;id&gt;</code>
<code>.kick &lt;id&gt; [reason]</code> — ban then immediately unban (removes
without a lasting ban)
<code>.mute &lt;id&gt;</code> · <code>.unmute &lt;id&gt;</code>
All of the above: reply to a user, or give their ID.

<code>.banall</code> · <code>.kickall</code> · <code>.muteall</code> · <code>.unmuteall</code>
No arguments needed — applies to every non-admin member of the current
chat. Can take a while in large groups.

<code>.tagall [message]</code>
Mentions every non-bot member in batches of 5, with a short delay
between batches. Optional custom text goes above the mentions.
Example: <code>.tagall Meeting in 10 minutes!</code>

<code>.tagallstop</code>
Interrupts a <code>.tagall</code> that's still running.

<code>.tagme</code>
Mentions just yourself — no arguments.
""",

    "warn": """
⚠️ <b>Warn System</b>
━━━━━━━━━━━━━━━━━━━━
Auto-bans a user after 3 warns in the same chat.

<code>.warn &lt;id&gt; [reason]</code>
Reply to a user, or give their ID + optional reason, to add a warn.

<code>.unwarn &lt;id&gt;</code>
Removes that user's most recent warn.

<code>.warns [id]</code>
Shows warns for the user you reply to / give an ID for — or your own,
if you don't specify anyone.

<code>.resetwarns &lt;id&gt;</code>
Clears all warns for that user in this chat.
""",

    "broadcast": """
📢 <b>Broadcast</b>
━━━━━━━━━━━━━━━━━━━━

<code>.broadcast &lt;text&gt;</code>
Sends that text to every chat the account is currently in.

<code>.broadcast</code> (reply to a message)
Copies that message to every chat instead of plain text — useful for
forwarding media, formatting, etc.
""",

    "sha": """
📜 <b>Shayari / Love</b>
━━━━━━━━━━━━━━━━━━━━
<code>.sha</code> and <code>.love</code> both work the same four ways
(love uses love-themed lines instead):

<code>.sha</code> (reply to someone)
Sends one shayari tagging just that person.

<code>.sha</code> (no reply, no arguments)
Sends one shayari tagging the whole group, once.

<code>.sha 20</code>
Starts a recurring broadcast every 20 minutes (10-minute minimum),
tagging a batch of members each time.

<code>.sha stop</code>
Stops the recurring broadcast in this chat.

100 unique original lines each for shayari and love.
""",

    "bro": """
👋 <b>Casual</b>
━━━━━━━━━━━━━━━━━━━━

<code>.bro</code> in a private chat (DM)
Sends a random casual message right there, no arguments needed.

<code>.bro</code> in a group (reply to someone)
Sends the message tagging that specific person.

<code>.bro</code> in a group with no reply just shows a usage note —
it never messages the whole group, since these are meant for one person.
""",

    "chat": """
🧹 <b>Chat Tools</b>
━━━━━━━━━━━━━━━━━━━━

<code>.del</code> (reply to a message)
Deletes that message (and your command).

<code>.purge</code> (reply to a message)
Deletes every message from the one you replied to, up through your
<code>.purge</code> command itself.
""",

    "fun": """
🎨 <b>Fun Animations</b>
━━━━━━━━━━━━━━━━━━━━
No arguments — just send the command and watch:

<code>.cat</code> — walking cat animation
<code>.rose</code> — a rose grows, then blooms into ASCII art
<code>.hacker</code> — "hacking" animation + ASCII art
<code>.error</code> — fake system-crash animation + ASCII art
<code>.butterfly</code> — draws a butterfly
<code>.myson</code> — a little ASCII scene
<code>.heart</code> — cycling color-heart animation

The final art stays in the chat once the animation finishes.
""",

    "utility": """
⚙️ <b>Utility</b>
━━━━━━━━━━━━━━━━━━━━

<code>.ping</code>
Shows response time in milliseconds.

<code>.alive</code>
Confirms the bot is running.

<code>.id</code> (optionally reply to someone)
Shows the current chat's ID, and either your ID or the replied user's ID.

<code>.info</code> (reply to someone, give a username/ID, or alone for
yourself)
Shows detailed info: ID, username, DC ID, premium status, chat role,
and warn count in this chat.

<code>.help</code>
This menu. <code>.help &lt;category&gt;</code> for full details on any section.
""",
}


@app.on_message(cmd("help"))
@sudo_only
async def help_cmd(client, message: Message):
    if len(message.command) > 1:
        key = message.command[1].lower()
        page = HELP_PAGES.get(key)
        if not page:
            await message.reply_text(
                f"No help page for `{key}`. Send `.help` to see valid categories."
            )
            return
        await message.reply_text(page)
        return

    await message.reply_text(HELP_INDEX)
