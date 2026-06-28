"""LoginToken — a short-lived, single-use magic-link token.

We store only the SHA-256 *hash* of the token, never the token itself. If the database
ever leaked, the stored hashes can't be turned back into working login links — same
reasoning as hashing passwords.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk


class LoginToken(Base, TimestampMixin):
    __tablename__ = "login_token"

    id: Mapped[uuid.UUID] = uuid_pk()
    # SHA-256 hex digest of the raw token (64 chars).
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Set the moment the token is redeemed, so it can never be reused.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
