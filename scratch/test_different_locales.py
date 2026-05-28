import sys
import os
import json
import requests

sys.path.append(os.getcwd())

from src.data_acquisition.browser_scraper import build_find_panorama_by_id_request_url

# We will test both panoramas with various locales
panos = ["Qj5sMj8OxrGksOMra1DK1A", "zpVIs8QgJa887h8HqCBIXw"]
locales = ["es-MX", "es-419", "en-US"]

headers = {
    "Referer": "https://www.google.com/maps/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for pano in panos:
    print(f"\n=================== PANO: {pano} ===================")
    for locale in locales:
        url = build_find_panorama_by_id_request_url(pano, locale=locale)
        # Force exact gl and hl if needed
        if locale == "es-419":
            url = url.replace("hl=es&gl=419", "hl=es-419&gl=mx")
            url = url.replace("!2ses!2s419", "!2ses-419!2smx")
        elif locale == "es-MX":
            url = url.replace("hl=es&gl=MX", "hl=es-419&gl=mx")
            url = url.replace("!2ses!2sMX", "!2ses-419!2smx")
            
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Locale: {locale}")
        print(f"Status Code: {resp.status_code}")
        snippet = resp.text[:200].replace('\n', ' ')
        print(f"Response: {snippet}")
