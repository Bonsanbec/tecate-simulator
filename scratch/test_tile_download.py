import sys
import os
import requests

def test():
    pano_id = "YqZ655EaY28-bpxFBEMLXw"
    zoom = 3
    x, y = 0, 0
    
    url_template = "https://streetviewpixels-pa.googleapis.com/v1/tile"
    headers = {
        "Referer": "https://www.google.com/maps/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    params = {
        "cb_client": "maps_sv.tactile",
        "panoid": pano_id,
        "x": str(x),
        "y": str(y),
        "zoom": str(zoom),
        "nbt": "1",
        "fover": "2"
    }
    
    print(f"Testing tile download from: {url_template}")
    print(f"Params: {params}")
    
    resp = requests.get(url_template, params=params, headers=headers, timeout=10)
    print(f"Response Status: {resp.status_code}")
    print(f"Response Length: {len(resp.content)} bytes")
    
    # Try different zoom levels
    for z in [0, 1, 2, 3]:
        p = params.copy()
        p["zoom"] = str(z)
        r = requests.get(url_template, params=p, headers=headers, timeout=10)
        print(f"Zoom {z}: Status = {r.status_code}, Length = {len(r.content)}")
        
    # Try alternative Google tile server URL templates
    alt_templates = [
        "https://lh3.ggpht.com/p/",
        "https://lh4.googleusercontent.com/cbk",
        "https://cbk0.google.com/cbk"
    ]
    for alt in alt_templates:
        try:
            # For lh3/lh4, the format might be different
            # For cbk: cb_client=maps_sv, panoid, zoom, x, y
            p = {
                "output": "tile",
                "panoid": pano_id,
                "zoom": "3",
                "x": "0",
                "y": "0",
                "cb_client": "maps_sv"
            }
            r = requests.get(alt, params=p, headers=headers, timeout=10)
            print(f"Alt Server {alt}: Status = {r.status_code}, Length = {len(r.content)}")
        except Exception as e:
            print(f"Alt Server {alt} error: {e}")

if __name__ == "__main__":
    test()
