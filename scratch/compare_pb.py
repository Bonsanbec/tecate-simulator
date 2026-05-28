import sys
import os

sys.path.append(os.getcwd())

from src.data_acquisition.browser_scraper import build_find_panorama_by_id_request_url as our_build
from streetlevel.streetview.api import build_find_panorama_by_id_request_url as streetlevel_build

panoid = "Qj5sMj8OxrGksOMra1DK1A"

our_url = our_build(panoid)
streetlevel_url = streetlevel_build(panoid, False, "en")

print("OUR URL:")
print(our_url)
print("\nSTREETLEVEL URL:")
print(streetlevel_url)

print(f"\nAre they identical? {our_url == streetlevel_url}")
