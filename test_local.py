import os
import sys
from dotenv import load_dotenv

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from modules.url_parser import GoogleMapsURLParser
from modules.scraper import GoogleMapsScraper
from modules.ai_analyzer import AIAnalyzer
from modules.line_messenger import LineMessenger

# Load environment variables
load_dotenv()

def test_pipeline(url):
    print(f"--- Testing Pipeline for URL: {url} ---")
    
    # 1. Parse URL
    print("1. Parsing URL...")
    clean_url = GoogleMapsURLParser.get_clean_url(url)
    print(f"   Clean URL: {clean_url}")
    
    if not clean_url:
        print("   Failed to parse URL.")
        return

    # 2. Scrape Data
    print("2. Scraping Data (this might take a few seconds)...")
    scraper = GoogleMapsScraper(headless=False) # Run with head to see what's happening
    reviews = scraper.scrape_reviews(clean_url, max_reviews=10)
    print(f"   Scraped {len(reviews)} reviews.")
    
    if not reviews:
        print("   Failed to scrape reviews.")
        return

    # 3. Analyze with AI
    print("3. Analyzing with AI...")
    analyzer = AIAnalyzer()
    restaurant_name = "測試餐廳"
    analysis_result = analyzer.analyze_reviews(reviews, restaurant_name=restaurant_name)
    print("   Analysis Result:")
    print(analysis_result)
    
    # 4. Generate Flex Message (Just print the JSON)
    print("4. Generating Flex Message...")
    flex_message = LineMessenger.create_analysis_flex_message(analysis_result, restaurant_name, clean_url)
    print("   Flex Message generated successfully.")

if __name__ == "__main__":
    # Example URL (You can change this to a real one)
    # This is a random restaurant link for testing
    test_url = "https://maps.app.goo.gl/vJz8z8z8z8z8z8z8" # Invalid link placeholder
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        print("Please provide a Google Maps URL as an argument, or input one now:")
        user_url = input("URL: ").strip()
        if user_url:
            test_url = user_url
        
    test_pipeline(test_url)
