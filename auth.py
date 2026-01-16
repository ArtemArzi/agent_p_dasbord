"""Authentication logic and middleware."""

import bcrypt
from functools import wraps
from nicegui import app, ui
from data import get_user_by_email
from models import User


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


async def authenticate(email: str, password: str) -> User | None:
    import logging

    logger = logging.getLogger(__name__)

    email = email.strip().lower()
    password = password.strip()

    logger.info(f"[AUTH] Attempting login for: {email}")

    user_data = get_user_by_email(email)

    if not user_data:
        return None

    stored_hash = user_data.get("encrypted_password", "")
    if not stored_hash:
        return None

    if not verify_password(password, stored_hash):
        return None

    logger.info(f"[AUTH] Login successful for: {email}")
    return User(**user_data)


def require_auth():
    """
    Decorator for protected pages.
    Redirects to /login if user is not authenticated.
    """

    def decorator(page_func):
        @wraps(page_func)
        async def wrapper(*args, **kwargs):
            if not app.storage.user.get("authenticated"):
                ui.navigate.to("/login")
                return
            return await page_func(*args, **kwargs)

        return wrapper

    return decorator


async def logout():
    """Clear user session and redirect to login."""
    app.storage.user.clear()
    ui.navigate.to("/login")
