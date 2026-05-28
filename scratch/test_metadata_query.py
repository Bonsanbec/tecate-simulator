import sys
import os
import json
import requests
from src.data_acquisition.browser_scraper import GoogleStreetViewScraper

def test():
    scraper = GoogleStreetViewScraper(cache_dir="data/raw_scraped")
    
    # 1. Query by coordinate
    print("Querying by coordinate near Parque Hidalgo...")
    meta_coord = scraper.fetch_public_metadata(lat=32.573229, lon=-116.626536)
    print("Result by coordinate:")
    print(json.dumps(meta_coord, indent=4))
    
    # 2. Query by pano_id
    pano_id = "zpVIs8QgJa887h8HqCBIXw"
    print(f"\nQuerying by pano_id: {pano_id}...")
    meta_pano = scraper.fetch_public_metadata(pano_id=pano_id)
    print("Result by pano_id:")
    print(json.dumps(meta_pano, indent=4))

if __name__ == "__main__":
    test()
