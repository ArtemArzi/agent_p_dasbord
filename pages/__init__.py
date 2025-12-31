"""Pages package."""

from pages import login
from .overview import overview_page
from .sessions import sessions_page
from .wishlist import wishlist_page
from .settings import settings_page

__all__ = ["login_page", "overview_page", "sessions_page", "wishlist_page", "settings_page"]
