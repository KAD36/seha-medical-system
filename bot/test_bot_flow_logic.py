#!/usr/bin/env python3
"""Focused tests for the Telegram nationality and subscription UX."""

import asyncio
import os
import sys
from pathlib import Path

_test_environment = {
    "DATABASE_URL": "sqlite:///:memory:",
    "BOT_TOKEN": "123456:test-token",
    "ADMIN_USER_ID": "123",
    "ADMIN_USER_IDS": "123,456",
}
_previous_environment = {key: os.environ.get(key) for key in _test_environment}
os.environ.update(_test_environment)
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bot_updated as bot  # noqa: E402
from catalog import DEFAULT_NATIONALITY_BUTTON  # noqa: E402

for _key, _value in _previous_environment.items():
    if _value is None:
        os.environ.pop(_key, None)
    else:
        os.environ[_key] = _value


class FakeUser:
    id = 123


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))


class FakeUpdate:
    def __init__(self, text=""):
        self.effective_user = FakeUser()
        self.message = FakeMessage(text)
        self.effective_message = self.message
        self.effective_chat = type("Chat", (), {"type": "private"})()
        self.callback_query = None


def test_subscription_contact_is_yousef():
    assert bot.SUBSCRIPTION_CONTACT_URL == "https://t.me/Yousef_sbri"


def test_both_configured_accounts_are_admins(monkeypatch):
    monkeypatch.setattr(bot, "ADMIN_USER_IDS", ("123", "456"))
    assert bot._is_admin(123) is True
    assert bot._is_admin(456) is True
    assert bot._is_admin(789) is False


def test_default_saudi_button_fills_both_languages(monkeypatch):
    update = FakeUpdate(DEFAULT_NATIONALITY_BUTTON)
    bot.user_data[123] = {"state": bot.STATES["NATIONALITY_AR"], "data": {}}
    next_step = {"called": False}

    async def allow(_update):
        return True

    async def fake_next(_update, _context):
        next_step["called"] = True

    monkeypatch.setattr(bot, "ensure_authorized", allow)
    monkeypatch.setattr(bot, "ask_employer_ar", fake_next)
    asyncio.run(bot.handle_message(update, None))

    assert bot.user_data[123]["data"]["nationality_ar"] == "سعودي"
    assert bot.user_data[123]["data"]["nationality_en"] == "Saudi Arabia"
    assert next_step["called"] is True


def test_empty_doctor_list_keeps_manual_entry_button():
    markup = bot._catalog_markup([], "doctor", 0)
    assert len(markup.inline_keyboard) == 1
    assert markup.inline_keyboard[0][0].callback_data == "doctor_custom"
