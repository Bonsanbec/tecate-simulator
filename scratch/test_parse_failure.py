import sys
import os
import json
import requests

sys.path.append(os.getcwd())

from src.data_acquisition.browser_scraper import build_find_panorama_by_id_request_url

panoid = "zpVIs8QgJa887h8HqCBIXw"
# Use es-MX directly
url = build_find_panorama_by_id_request_url(panoid, locale="es-MX")

print(f"Raw URL: {url}")
resp = requests.get(url, timeout=10)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text[:300]}")
