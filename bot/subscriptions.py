"""Persistent monthly access subscriptions for the Telegram bot."""

import calendar
import os
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    insert,
    select,
    update,
)


def _database_url() -> str:
    value = os.environ.get("DATABASE_URL", "").strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    if value:
        return value
    return "sqlite:///src/database/app.db"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def add_calendar_months(value: datetime, months: int) -> datetime:
    """Add calendar months while retaining a valid day of month."""
    zero_based_month = value.month - 1 + months
    year = value.year + zero_based_month // 12
    month = zero_based_month % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class SubscriptionStore:
    def __init__(self):
        self.engine = create_engine(_database_url(), pool_pre_ping=True)
        self.metadata = MetaData()
        self.subscriptions = Table(
            "bot_subscriptions",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("telegram_user_id", String, nullable=False, unique=True, index=True),
            Column("username", String),
            Column("first_name", String),
            Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
            Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
            Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        )
        self.events = Table(
            "subscription_events",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("telegram_user_id", String, nullable=False, index=True),
            Column("action", String, nullable=False),
            Column("months", Integer),
            Column("performed_by", String, nullable=False),
            Column("occurred_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        )
        self.metadata.create_all(self.engine)

    def get(self, telegram_user_id) -> dict | None:
        statement = select(self.subscriptions).where(
            self.subscriptions.c.telegram_user_id == str(telegram_user_id)
        )
        with self.engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if not row:
            return None
        result = dict(row)
        result["expires_at"] = _aware(result["expires_at"])
        return result

    def is_active(self, telegram_user_id) -> bool:
        record = self.get(telegram_user_id)
        return bool(record and record["expires_at"] > _utc_now())

    def remember_user(self, telegram_user_id, username=None, first_name=None) -> None:
        user_id = str(telegram_user_id)
        values = {
            "username": (username or "")[:255] or None,
            "first_name": (first_name or "")[:255] or None,
        }
        with self.engine.begin() as connection:
            exists = connection.execute(
                select(self.subscriptions.c.id).where(
                    self.subscriptions.c.telegram_user_id == user_id
                )
            ).first()
            if exists:
                connection.execute(
                    update(self.subscriptions)
                    .where(self.subscriptions.c.telegram_user_id == user_id)
                    .values(**values, updated_at=func.now())
                )
            else:
                connection.execute(
                    insert(self.subscriptions).values(
                        telegram_user_id=user_id,
                        expires_at=_utc_now(),
                        **values,
                    )
                )

    def grant(self, telegram_user_id, months: int, performed_by) -> datetime:
        if not 1 <= months <= 12:
            raise ValueError("months must be between 1 and 12")
        user_id = str(telegram_user_id)
        now = _utc_now()
        with self.engine.begin() as connection:
            row = connection.execute(
                select(self.subscriptions).where(
                    self.subscriptions.c.telegram_user_id == user_id
                ).with_for_update()
            ).mappings().first()
            current_expiry = _aware(row["expires_at"]) if row else None
            base = current_expiry if current_expiry and current_expiry > now else now
            expires_at = add_calendar_months(base, months)
            if row:
                connection.execute(
                    update(self.subscriptions)
                    .where(self.subscriptions.c.telegram_user_id == user_id)
                    .values(expires_at=expires_at, updated_at=func.now())
                )
            else:
                connection.execute(
                    insert(self.subscriptions).values(
                        telegram_user_id=user_id,
                        expires_at=expires_at,
                    )
                )
            connection.execute(
                insert(self.events).values(
                    telegram_user_id=user_id,
                    action="grant",
                    months=months,
                    performed_by=str(performed_by),
                )
            )
        return expires_at

    def revoke(self, telegram_user_id, performed_by) -> bool:
        user_id = str(telegram_user_id)
        with self.engine.begin() as connection:
            result = connection.execute(
                update(self.subscriptions)
                .where(self.subscriptions.c.telegram_user_id == user_id)
                .values(expires_at=_utc_now(), updated_at=func.now())
            )
            if result.rowcount:
                connection.execute(
                    insert(self.events).values(
                        telegram_user_id=user_id,
                        action="revoke",
                        performed_by=str(performed_by),
                    )
                )
        return result.rowcount > 0

    def list_active(self, limit: int = 100) -> list[dict]:
        statement = (
            select(self.subscriptions)
            .where(self.subscriptions.c.expires_at > _utc_now())
            .order_by(self.subscriptions.c.expires_at.asc())
            .limit(limit)
        )
        with self.engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        result = []
        for row in rows:
            item = dict(row)
            item["expires_at"] = _aware(item["expires_at"])
            result.append(item)
        return result
