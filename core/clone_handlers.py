"""
Shared logic for attaching the standard command set (utility + VC) onto any
extra Pyrogram Client — used by both `.clone` (bot-token clones) and
`.login` (user-session clones), so both share one implementation.
"""
from pyrogram import Client
from pyrogram.handlers import MessageHandler

from modules.utils.basics import ping_cmd, alive_cmd, id_cmd, help_cmd, cmd as u_cmd
from modules.vc.play import play_cmd, cmd as vc_cmd
from modules.vc.controls import (
    pause_cmd, resume_cmd, mute_cmd, unmute_cmd, stop_cmd, skip_cmd, cmd as vcc_cmd,
)


def register_common_handlers(client: Client):
    client.add_handler(MessageHandler(ping_cmd, u_cmd("ping")))
    client.add_handler(MessageHandler(alive_cmd, u_cmd(["alive", "start"])))
    client.add_handler(MessageHandler(id_cmd, u_cmd("id")))
    client.add_handler(MessageHandler(help_cmd, u_cmd("help")))

    client.add_handler(MessageHandler(play_cmd, vc_cmd(["play", "vply", "cplay", "cvply"])))
    client.add_handler(MessageHandler(pause_cmd, vcc_cmd("pause")))
    client.add_handler(MessageHandler(resume_cmd, vcc_cmd("resume")))
    client.add_handler(MessageHandler(mute_cmd, vcc_cmd("vmute")))
    client.add_handler(MessageHandler(unmute_cmd, vcc_cmd("vunmute")))
    client.add_handler(MessageHandler(stop_cmd, vcc_cmd("stop")))
    client.add_handler(MessageHandler(skip_cmd, vcc_cmd("skip")))
