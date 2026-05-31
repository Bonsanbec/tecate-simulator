import requests

overpass_url = "https://overpass-api.de/api/interpreter"
bbox = (32.521704, -116.681499, 32.580233, -116.510525)

query = f"""[out:json][timeout:15];
(
  way["highway"~"trunk|trunk_link"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);
out body;
>;
out skel qt;"""

headers = {
    "User-Agent": "TecateSimulatorReconstructor/1.0 (contact: hakkindavid@github)"
}

print("Requesting trunk highways from Overpass API...")
try:
    resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=15)
    if resp.status_code == 200:
        elements = resp.json().get("elements", [])
        ways = [el for el in elements if el["type"] == "way"]
        print(f"Found {len(ways)} trunk ways!")
        for idx, w in enumerate(ways[:15]):
            tags = w.get("tags", {})
            name = tags.get("name", f"Unnamed trunk ({w['id']})")
            print(f"  Trunk Way {idx}: id={w['id']}, name='{name}', highway='{tags.get('highway')}'")
    else:
        print(f"Overpass returned status: {resp.status_code}")
        print(resp.text[:500])
except Exception as e:
    print(f"Query failed: {e}")
