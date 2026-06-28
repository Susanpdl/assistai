"""FastAPI dependencies for authentication and authorization.

- `get_current_user` turns the session cookie into a `User`, or 401s.
- `require_role(role)` builds a dependency that 403s unless the user has that role.
"""

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.sessions import get_session_user_id
from app.config import settings
from app.db import get_db
from app.models.enums import Role
from app.models.identity import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    session_id = request.cookies.get(settings.session_cookie_name)
    user_id = get_session_user_id(session_id) if session_id else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user = db.get(User, uuid.UUID(user_id))
    except (ValueError, TypeError):
        user = None
    if user is None:
        # Session points at a user that no longer exists.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_role(role: Role) -> Callable[..., User]:
    """Dependency factory: only allow users whose role matches."""

    def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {role.value} role",
            )
        return user

    return _guard
