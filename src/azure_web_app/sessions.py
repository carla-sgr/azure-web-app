"""Signed cookies backed by database login sessions."""

import functools
import hashlib
import hmac
import os

from flask import Flask, Response, g, redirect, request, url_for

from azure_web_app._constants import (
    APP_SECRET_VARIABLE,
    SESSION_COOKIE_NAME,
    SESSION_LIFETIME_SECONDS,
)
from azure_web_app.db import get_db


def get_app_secret() -> bytes:
    """Read the cookie-signing secret from the environment."""
    return os.environ[APP_SECRET_VARIABLE].encode()


def running_on_azure() -> bool:
    """Check whether the app is running on Azure."""
    return "WEBSITE_HOSTNAME" in os.environ


def compute_signature(session_id: str) -> str:
    """Create an HMAC signature for a session ID."""
    return hmac.new(
        get_app_secret(),
        session_id.encode(),
        hashlib.sha256,
    ).hexdigest()


def sign_session_id(session_id: str) -> str:
    """Combine a session ID and its signature into a cookie value."""
    return f"{session_id}:{compute_signature(session_id)}"


def verify_session_cookie(cookie: str | None) -> str | None:
    """Return the session ID only when its signature is valid."""
    if not cookie:
        return None

    session_id, separator, signature = cookie.partition(":")
    if not session_id or not separator:
        return None

    expected = compute_signature(session_id)
    if hmac.compare_digest(signature.encode(), expected.encode()):
        return session_id

    return None


def set_session_cookie(response: Response, session_id: str) -> None:
    """Set the signed session cookie on a response."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        value=sign_session_id(session_id),
        max_age=SESSION_LIFETIME_SECONDS,
        httponly=True,
        samesite="Lax",
        secure=running_on_azure(),
    )


def clear_session_cookie(response: Response) -> None:
    """Tell the browser to delete its session cookie."""
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        httponly=True,
        samesite="Lax",
        secure=running_on_azure(),
    )


def load_current_user() -> None:
    """Load the user for a valid, unexpired session before each request."""
    g.current_user = None

    if request.endpoint == "static":
        return

    session_id = verify_session_cookie(
        request.cookies.get(SESSION_COOKIE_NAME)
    )
    if session_id is None:
        return

    database = get_db()
    user = database.get_session_user(session_id)
    if user is None:
        return

    if user.is_expired:
        database.delete_session(session_id)
        return

    g.current_user = user


def inject_current_user() -> dict:
    """Make the current user available to every Jinja template."""
    return {"current_user": g.get("current_user")}


def login_required(view):
    """Redirect logged-out visitors to the homepage."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if g.get("current_user") is None:
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapper


def setup_sessions(app: Flask) -> None:
    """Register the session-loading and template hooks."""
    app.before_request(load_current_user)
    app.context_processor(inject_current_user)