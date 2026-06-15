"""
Scrapers package initialization.
Registers enabled scrapers at startup.
"""

from utils.scrapers.youtube_plugin import youtube_plugin
from utils.scraper_plugin import scraper_registry


def init_scrapers():
    """Initialize and register all enabled scrapers."""
    # Register YouTube (enabled by default)
    scraper_registry.register("youtube", youtube_plugin, enabled=True)
    print("[Scrapers] Initialized plugin registry")


# Auto-initialize when module is imported
init_scrapers()
