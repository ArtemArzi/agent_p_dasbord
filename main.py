"""Agent P Dashboard - NiceGUI Application Entry Point."""

from nicegui import app, ui
from config import settings

# Import pages (registers routes via decorators)
from pages import login
from pages import overview
from pages import sessions
from pages import wishlist
from pages import settings as settings_page_module
from pages import users



@ui.page("/")
def index():
    """Root page - redirect to login."""
    ui.navigate.to("/login")


def main():
    """Run the NiceGUI application."""
    from pathlib import Path
    
    static_dir = Path(__file__).parent / "static"
    favicon_path = static_dir / "favicon.png"
    
    app.add_static_files("/static", str(static_dir))
    ui.run(
        host=settings.app_host,
        port=settings.app_port,
        title="AMICA",
        storage_secret=settings.app_secret,
        reload=settings.debug,
        favicon=str(favicon_path) if favicon_path.exists() else "💜",
    )


if __name__ == "__main__":
    import sys
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 AMICA Dashboard stopped.")
        sys.exit(0)
