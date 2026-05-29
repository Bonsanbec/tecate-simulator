import sys
import os
import json
import requests

sys.path.append(os.getcwd())

from src.data_acquisition.browser_scraper import GoogleStreetViewScraper

scraper = GoogleStreetViewScraper()
lat, lon = 32.573229, -116.626536
pano_id = "zpVIs8QgJa887h8HqCBIXw"

print(f"Calling fetch_public_metadata(lat={lat}, lon={lon}, pano_id={pano_id})...")
meta = scraper.fetch_public_metadata(lat=lat, lon=lon, pano_id=pano_id)
print("Returned meta:")
print(json.dumps(meta, indent=4))
