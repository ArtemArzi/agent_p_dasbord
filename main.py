"""Agent P Dashboard - NiceGUI Application Entry Point."""

from nicegui import app, ui
from config import settings

# Import pages (registers routes via decorators)
from pages import login
from pages import overview
from pages import sessions
from pages import wishlist
from pages import settings as settings_page_module


@ui.page("/")
def index():
    """Root page - redirect to login."""
    ui.navigate.to("/login")


def main():
    """Run the NiceGUI application."""
    ui.run(
        host=settings.app_host,
        port=settings.app_port,
        title="Agent P Dashboard",
        dark=True,
        storage_secret=settings.app_secret,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
