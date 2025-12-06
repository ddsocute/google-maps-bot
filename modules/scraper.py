import os
import googlemaps
import re
import requests

class GoogleMapsScraper:
    def __init__(self, headless=True):
        # We are now using Google Places API, so headless param is ignored but kept for compatibility
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            print("Warning: GOOGLE_MAPS_API_KEY not found.")
            self.client = None
        else:
            self.client = googlemaps.Client(key=self.api_key)

    def _extract_place_id_from_url(self, url):
        """
        Attempts to extract Place ID from a Google Maps URL.
        This is tricky because URLs vary.
        Strategy:
        1. If it's a long URL with 'place_id' param.
        2. If it's a CID (Customer ID), we might need to search by text.
        3. Most reliable: Use Text Search API with the URL or extracted name.
        """
        # Simplified approach: Use Text Search with the URL itself if it contains the name, 
        # or better, just search for the restaurant name if we can extract it.
        # But since we have the URL, we can use the Places Text Search API with the query set to the URL 
        # (sometimes works) or better, just use the URL to find the place.
        
        # Actually, the most robust way with the API is to use "Find Place From Text" 
        # inputting the phone number or name.
        # But we only have the URL.
        
        # Let's try to find the place using the text search with the URL.
        # Note: Searching with the full URL in 'query' often works in Google Maps, 
        # let's see if the API supports it.
        
        return None

    def scrape_reviews(self, url, max_reviews=5):
        """
        Fetches reviews using Google Places API.
        Note: The API typically returns up to 5 top reviews by default.
        To get more, we might need Premium data or specific sorting, but usually 5 is the limit for standard fetch.
        Wait, 'Place Details' returns up to 5 reviews. 
        """
        if not self.client:
            print("Error: Google Maps API Client not initialized.")
            return []

        print(f"Fetching data for: {url}")
        
        try:
            # Step 1: Find the Place ID
            # We use the 'find_place' method. 
            # Input type 'textquery' is versatile. We can try passing the URL or parts of it.
            # However, passing the raw URL might not always work.
            # Let's try to extract the name or just use the URL as the query.
            
            # Better strategy: Expand the URL first (already done in app.py), 
            # then regex extract the name if possible, or just search.
            
            # Let's try searching with the URL first.
            # If that fails, we might need to ask the user for the name, but that's bad UX.
            # Let's assume the URL is a standard share link.
            
            # Hack: Use the requests to get the title of the page, which is the restaurant name.
            try:
                response = requests.get(url, timeout=5)
                # Title format: "Restaurant Name - Google Maps"
                page_title = re.search(r'<title>(.*?)</title>', response.text).group(1)
                place_name = page_title.replace(' - Google Maps', '').strip()
                print(f"Extracted name: {place_name}")
            except:
                place_name = url # Fallback
            
            # Find Place
            places_result = self.client.find_place(
                input=place_name,
                input_type='textquery',
                fields=['place_id', 'name', 'formatted_address']
            )
            
            if not places_result or 'candidates' not in places_result or not places_result['candidates']:
                print("No place found via API.")
                return []
                
            place_id = places_result['candidates'][0]['place_id']
            print(f"Found Place ID: {place_id}")
            
            # Step 2: Get Place Details (Reviews)
            # Note: reviews field triggers a specific SKU.
            place_details = self.client.place(
                place_id=place_id,
                fields=['name', 'rating', 'reviews', 'user_ratings_total']
            )
            
            if 'result' not in place_details:
                return []
                
            result = place_details['result']
            api_reviews = result.get('reviews', [])
            
            # Format reviews
            formatted_reviews = []
            for r in api_reviews:
                formatted_reviews.append({
                    'name': r.get('author_name', 'Unknown'),
                    'rating': r.get('rating', 0),
                    'time': r.get('relative_time_description', ''),
                    'text': r.get('text', '')
                })
                
            return formatted_reviews

        except Exception as e:
            print(f"Google Maps API Error: {e}")
            return []
