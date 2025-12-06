import re
import requests
from urllib.parse import urlparse, parse_qs

class GoogleMapsURLParser:
    @staticmethod
    def extract_url(text):
        """Extracts the first URL from a text string."""
        url_pattern = r'(https?://[^\s]+)'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def expand_url(short_url):
        """Expands a shortened Google Maps URL to the full URL."""
        try:
            response = requests.head(short_url, allow_redirects=True, timeout=10)
            return response.url
        except Exception as e:
            print(f"Error expanding URL: {e}")
            return None

    @staticmethod
    def parse_place_id_or_coords(full_url):
        """Extracts Place ID or coordinates from the full Google Maps URL."""
        # This is a simplified parser, might need more robust logic for different URL formats
        # Example 1: https://www.google.com/maps/place/Restaurant+Name/@25.033,121.565,17z/data=...!3m1!4b1!4m6!3m5!1s0x3442abb...
        # Example 2: https://www.google.com/maps/search/?api=1&query=...&query_place_id=...
        
        parsed = urlparse(full_url)
        
        # Try to find !1s... which usually indicates the Place ID (CID) or similar identifier in the data param
        # But for scraping, the full URL is often enough.
        # For API, we might need specific IDs.
        
        return full_url

    @staticmethod
    def get_clean_url(text):
        """Main method to process input text and return a clean, expanded URL."""
        raw_url = GoogleMapsURLParser.extract_url(text)
        if not raw_url:
            return None
            
        if "maps.app.goo.gl" in raw_url:
            return GoogleMapsURLParser.expand_url(raw_url)
            
        return raw_url
