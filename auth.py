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
        return bcrypt.checkpw(
            password.encode(), 
            hashed.encode()
        )
    except Exception:
        return False


async def authenticate(email: str, password: str) -> User | None:
    """
    Authenticate user by email and password.
    Returns User object if successful, None otherwise.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[AUTH] Attempting login for email: {email}")
    
    user_data = get_user_by_email(email)
    
    if not user_data:
        logger.warning(f"[AUTH] User not found: {email}")
        return None
    
    logger.info(f"[AUTH] User found: {user_data.get('email')}, role: {user_data.get('role')}")
    
    stored_hash = user_data.get("encrypted_password", "")
    if not stored_hash:
        logger.warning(f"[AUTH] No password hash for user: {email}")
        return None
    
    logger.info(f"[AUTH] Verifying password for: {email}")
    if not verify_password(password, stored_hash):
        logger.warning(f"[AUTH] Password mismatch for: {email}")
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
