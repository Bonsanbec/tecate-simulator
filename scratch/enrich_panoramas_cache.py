import os
import json
import time
from src.data_acquisition.browser_scraper import GoogleStreetViewScraper

def enrich_cache():
    cache_path = "data/panoramas_cache.json"
    if not os.path.exists(cache_path):
        print(f"[Error] Cache path not found at: {cache_path}")
        return

    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)

    print(f"[Enrichment] Loaded {len(cache)} panoramas from cache.")
    
    scraper = GoogleStreetViewScraper(headless=True)
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, (pano_id, data) in enumerate(cache.items()):
        # Check if already has projection_yaw/pano_yaw, road_name, adjacent_links, timeline
        if "projection_yaw" in data and "adjacent_links" in data and "timeline" in data:
            # Also prune any legacy virtual camera parameters that might have slipped into the cache
            for prop in ["hfov", "vfov", "camera_height_m", "focal_length_px", "optical_center", "intrinsic_matrix"]:
                if prop in data:
                    data.pop(prop)
            skipped_count += 1
            continue

        print(f"[{idx+1}/{len(cache)}] Enriching {pano_id}...")
        
        # Prune legacy virtual camera parameters if any
        for prop in ["hfov", "vfov", "camera_height_m", "focal_length_px", "optical_center", "intrinsic_matrix"]:
            if prop in data:
                data.pop(prop)

        # Fetch metadata using unauthenticated client endpoint
        meta = scraper.fetch_public_metadata(pano_id=pano_id)
        if not meta:
            # If standard request fails, try coordinates if available
            lat = data.get("latitude")
            lon = data.get("longitude")
            if lat and lon:
                meta = scraper.fetch_public_metadata(lat=lat, lon=lon)

        if meta:
            proj_yaw = meta.get("projection_yaw")
            data.update({
                "latitude": meta.get("latitude", data.get("latitude")),
                "longitude": meta.get("longitude", data.get("longitude")),
                "altitude": meta.get("altitude", data.get("altitude")),
                "date": meta.get("date", data.get("date", "")),
                "pitch": meta.get("pitch", data.get("pitch")),
                "roll": meta.get("roll", data.get("roll")),
                "projection_yaw": proj_yaw,
                "pano_yaw": proj_yaw,
                "road_name": meta.get("road_name", ""),
                "adjacent_links": meta.get("adjacent_links", []),
                "timeline": meta.get("timeline", [])
            })
            updated_count += 1
            # Save every 20 entries to prevent complete progress loss
            if updated_count % 20 == 0:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache, f, indent=4)
                print(f"[Autosave] Written progress to {cache_path}")
        else:
            print(f"[Warning] Failed to fetch metadata for {pano_id}. Not updating.")
            failed_count += 1
            
        time.sleep(0.1)  # Polite delay

    # Save final cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)
        
    print("=" * 50)
    print("Enrichment process completed!")
    print(f"Total entries: {len(cache)}")
    print(f"Already fully enriched: {skipped_count}")
    print(f"Successfully enriched: {updated_count}")
    print(f"Failed / Not updated: {failed_count}")
    print("=" * 50)

if __name__ == "__main__":
    enrich_cache()
