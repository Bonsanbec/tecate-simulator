import sys
import os
import json
import logging

sys.path.append(os.getcwd())

# Enable logging to stdout
logging.basicConfig(level=logging.INFO)

from src.data_acquisition.browser_scraper import GoogleStreetViewScraper

cache_dir = "data/raw_scraped"
scraper = GoogleStreetViewScraper(cache_dir=cache_dir, headless=False)

seed_lat = 32.573229
seed_lon = -116.626536

print("Starting E2E priority network crawl...")
nodes = scraper.crawl_priority_network(seed_lat, seed_lon, max_nodes=5)
print(f"\nCrawl complete! Discovered {len(nodes)} nodes:")
for node in nodes:
    print(f" - {node['pano_id']}: {node['date']} at ({node['latitude']}, {node['longitude']})")
