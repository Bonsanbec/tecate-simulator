import sys
import os
import requests

panos = ["zpVIs8QgJa887h8HqCBIXw", "Qj5sMj8OxrGksOMra1DK1A"]
zooms = [1, 2, 3, 4]

url_template = "https://streetviewpixels-pa.googleapis.com/v1/tile"

headers = {
    "Referer": "https://www.google.com/maps/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for pano in panos:
    print(f"\n=================== PANO: {pano} ===================")
    for zoom in zooms:
        params = {
            "cb_client": "maps_sv.tactile",
            "panoid": pano,
            "x": "0",
            "y": "0",
            "zoom": str(zoom),
            "nbt": "1",
            "fover": "2"
        }
        try:
            resp = requests.get(url_template, params=params, headers=headers, timeout=10)
            print(f"Zoom {zoom}: Status Code={resp.status_code}, Size={len(resp.content)} bytes")
            if resp.status_code != 200:
                print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Zoom {zoom} error: {e}")
