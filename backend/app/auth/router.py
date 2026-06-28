"""Auth endpoints: request a magic link, verify it, who-am-i, and logout."""

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.email import EmailSender, get_email_sender, send_magic_link
from app.auth.rate_limit import too_many_requests
from app.auth.schemas import LoginRequest, UserOut
from app.auth.sessions import create_session, delete_session
from app.auth.tokens import consume_login_token, create_login_token
from app.config import settings
from app.db import get_db
from app.models.enums import Role
from app.models.identity import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request", status_code=status.HTTP_200_OK)
def request_login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
) -> dict:
    """Email a magic link. Always returns 200 — even for unknown or rate-limited emails —
    so it can't be used to probe who has an account."""
    email = payload.email.lower()
    client_ip = request.client.host if request.client else "unknown"
    # Rate-limit by both email and IP; either tripping silently stops the send.
    limited = too_many_requests("auth_email", email) or too_many_requests("auth_ip", client_ip)
    if not limited:
        raw_token = create_login_token(db, email)
        link = f"{settings.api_base_url}/auth/verify?token={raw_token}"
        send_magic_link(sender, to=email, link=link)
    return {"status": "sent"}


@router.get("/verify")
def verify_login(token: str, db: Session = Depends(get_db)) -> Response:
    """Validate the token, find-or-create the user, start a session, redirect into the app."""
    email = consume_login_token(db, token)
    if email is None:
        # Bounce back to the frontend with an error flag rather than a bare 400.
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth=invalid", status_code=status.HTTP_303_SEE_OTHER
        )

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        role = Role.instructor if email in settings.instructor_email_set else Role.student
        user = User(email=email, name=email.split("@")[0], role=role)
        db.add(user)
        db.commit()
        db.refresh(user)

    session_id = create_session(str(user.id))
    response = RedirectResponse(url=settings.frontend_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        path="/",
    )
    return response


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, response: Response) -> dict:
    delete_session(request.cookies.get(settings.session_cookie_name, ""))
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"status": "logged_out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
