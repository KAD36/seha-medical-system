#!/usr/bin/env python3
"""Run the Flask website and Telegram webhook in one free Render service."""

import asyncio
import hashlib
import hmac
import logging
import os
import sys
from http import HTTPStatus
from pathlib import Path

import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Response, abort, request
from telegram import BotCommand, BotCommandScopeChat, Update


ROOT_DIR = Path(__file__).resolve().parent
BOT_DIR = ROOT_DIR / "bot"
sys.path.insert(0, str(BOT_DIR))

from bot_updated import build_application  # noqa: E402
from config import ADMIN_USER_IDS, BOT_TOKEN  # noqa: E402
from src.main import app as flask_app  # noqa: E402


telegram_application = None
webhook_secret = hashlib.sha256(BOT_TOKEN.encode("utf-8")).hexdigest()
logger = logging.getLogger(__name__)


@flask_app.post("/telegram-webhook")
async def telegram_webhook() -> Response:
    supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(supplied_secret, webhook_secret):
        abort(HTTPStatus.FORBIDDEN)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or telegram_application is None:
        abort(HTTPStatus.BAD_REQUEST)

    await telegram_application.update_queue.put(
        Update.de_json(data=payload, bot=telegram_application.bot)
    )
    return Response(status=HTTPStatus.OK)


async def main() -> None:
    global telegram_application

    if not BOT_TOKEN or not ADMIN_USER_IDS:
        raise RuntimeError("BOT_TOKEN and ADMIN_USER_IDS (or ADMIN_USER_ID) must be configured")

    external_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WEBHOOK_BASE_URL")
    if not external_url:
        raise RuntimeError("RENDER_EXTERNAL_URL or WEBHOOK_BASE_URL must be configured")

    telegram_application = build_application(polling=False)
    port = int(os.environ.get("PORT", "10000"))
    server = uvicorn.Server(
        uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            host="0.0.0.0",
            port=port,
            use_colors=False,
            access_log=True,
        )
    )

    async with telegram_application:
        await telegram_application.bot.set_webhook(
            url=f"{external_url.rstrip('/')}/telegram-webhook",
            allowed_updates=Update.ALL_TYPES,
            secret_token=webhook_secret,
        )
        public_commands = [
            BotCommand("start", "بدء استخدام البوت"),
            BotCommand("id", "عرض معرّف حسابك"),
            BotCommand("mystatus", "حالة اشتراكك"),
        ]
        await telegram_application.bot.set_my_commands(public_commands)
        admin_commands = public_commands + [
            BotCommand("subscriptions", "تعليمات إدارة الاشتراكات"),
            BotCommand("grant", "تفعيل أو تمديد اشتراك"),
            BotCommand("renew", "تمديد اشتراك شهرًا"),
            BotCommand("revoke", "إلغاء اشتراك"),
            BotCommand("substatus", "حالة اشتراك مستخدم"),
            BotCommand("subscribers", "الاشتراكات الفعالة"),
        ]
        for admin_id in ADMIN_USER_IDS:
            try:
                await telegram_application.bot.set_my_commands(
                    admin_commands,
                    scope=BotCommandScopeChat(chat_id=int(admin_id)),
                )
            except Exception:
                # A new admin may not have opened the bot yet. Authorization is
                # still active; the scoped command menu will be retried on restart.
                logger.warning("Could not configure one admin-scoped command menu")
        await telegram_application.start()
        await server.serve()
        await telegram_application.stop()


if __name__ == "__main__":
    asyncio.run(main())
