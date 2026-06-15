"""
scraper_plugin.py — Base plugin architecture for scrapers.

Allows multiple scraper implementations (YouTube, Dailymotion, etc.)
to be registered and enabled/disabled via configuration.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SearchContext(BaseModel):
    """Context parameters to narrow and focus YouTube searches for sports content."""
    
    # Core search parameters
    sport: str  # e.g., "cricket", "football", "basketball"
    keywords: str  # e.g., "IPL", "Premier League", "NBA"
    
    # Filtering parameters (all optional for flexible searching)
    duration_min: Optional[int] = None  # Min video duration in seconds (e.g., 120 for 2 min)
    duration_max: Optional[int] = None  # Max video duration in seconds (e.g., 1200 for 20 min)
    min_view_count: Optional[int] = None  # Min view count (e.g., 1000 to skip noise)
    uploaded_after: Optional[datetime] = None  # Only videos uploaded after this date
    channel_whitelist: Optional[List[str]] = None  # Only these channels (if provided)
    channel_blacklist: Optional[List[str]] = None  # Exclude these channels
    
    # Pagination
    max_results: int = 10  # How many results to return
    
    # Metadata tracking
    video_id: Optional[str] = None  # Original uploaded video ID (for audit trail)


class ScraperResult(BaseModel):
    """Standard result format from any scraper."""
    url: str
    title: str
    channel: str
    channel_url: str
    duration: int  # seconds
    view_count: int
    platform: str  # "youtube", "dailymotion", "twitter", etc.
    source: str  # "keyword_search", "channel_scan", "web_search", etc.
    sport: str
    keywords: str
    uploaded_date: Optional[datetime] = None


class ScraperPlugin(ABC):
    """Abstract base class for all scraper implementations."""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def search(self, context: SearchContext) -> List[ScraperResult]:
        """
        Search for video URLs using the provided context.
        
        Args:
            context: SearchContext with search parameters and filters
            
        Returns:
            List of ScraperResult objects
        """
        pass
    
    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        Check if a URL is a valid individual video page for this platform.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid video URL, False otherwise
        """
        pass
    
    def is_enabled(self) -> bool:
        """
        Override this to add runtime enable/disable logic.
        Default: enabled.
        """
        return True


class ScraperRegistry:
    """Registry to manage enabled scrapers at runtime."""
    
    def __init__(self):
        self._scrapers: dict[str, ScraperPlugin] = {}
        self._enabled: set[str] = set()
    
    def register(self, name: str, scraper: ScraperPlugin, enabled: bool = True):
        """Register a scraper plugin."""
        self._scrapers[name] = scraper
        if enabled and scraper.is_enabled():
            self._enabled.add(name)
        print(f"[ScraperRegistry] Registered {name} (enabled={name in self._enabled})")
    
    def enable(self, name: str):
        """Enable a scraper by name."""
        if name in self._scrapers:
            self._enabled.add(name)
    
    def disable(self, name: str):
        """Disable a scraper by name."""
        self._enabled.discard(name)
    
    def get_enabled_scrapers(self) -> dict[str, ScraperPlugin]:
        """Get all currently enabled scrapers."""
        return {name: self._scrapers[name] for name in self._enabled}
    
    def search_all(self, context: SearchContext) -> dict[str, List[ScraperResult]]:
        """
        Run all enabled scrapers and return results organized by scraper name.
        
        Args:
            context: SearchContext for the search
            
        Returns:
            Dictionary mapping scraper names to lists of results
        """
        results = {}
        for name, scraper in self.get_enabled_scrapers().items():
            try:
                print(f"[ScraperRegistry] Running {name}...")
                results[name] = scraper.search(context)
            except Exception as e:
                print(f"[ScraperRegistry] Error in {name}: {e}")
                results[name] = []
        return results


# Global registry instance
scraper_registry = ScraperRegistry()
