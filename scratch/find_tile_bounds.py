import requests

def test():
    pano_id = "YqZ655EaY28-bpxFBEMLXw"
    zoom = 3
    
    url_template = "https://streetviewpixels-pa.googleapis.com/v1/tile"
    headers = {
        "Referer": "https://www.google.com/maps/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Try different x, y bounds to see what returns 200 vs 404 or 400
    print("Scanning columns (y = 0):")
    for x in range(16):
        params = {
            "cb_client": "maps_sv.tactile",
            "panoid": pano_id,
            "x": str(x),
            "y": "0",
            "zoom": str(zoom),
            "nbt": "1",
            "fover": "2"
        }
        resp = requests.get(url_template, params=params, headers=headers)
        print(f"x = {x}: status = {resp.status_code}, len = {len(resp.content)}")
        
    print("\nScanning rows (x = 0):")
    for y in range(8):
        params = {
            "cb_client": "maps_sv.tactile",
            "panoid": pano_id,
            "x": "0",
            "y": str(y),
            "zoom": str(zoom),
            "nbt": "1",
            "fover": "2"
        }
        resp = requests.get(url_template, params=params, headers=headers)
        print(f"y = {y}: status = {resp.status_code}, len = {len(resp.content)}")

if __name__ == "__main__":
    test()
