import requests
import json

bbox = (32.563, -116.638, 32.583, -116.614) # central Tecate
overpass_url = "https://overpass-api.de/api/interpreter"
query = f"""
[out:json][timeout:15];
(
  way["highway"~"primary|secondary|tertiary|residential|unclassified"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);
out body;
>;
out skel qt;
"""
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.openstreetmap.org/"
}
try:
    print("Querying Overpass API...")
    resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=15)
    print("Status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        elements = data.get("elements", [])
        print("Number of elements:", len(elements))
        with open("scratch/osm_test.json", "w") as f:
            json.dump(data, f, indent=4)
except Exception as e:
    print("Error:", e)
