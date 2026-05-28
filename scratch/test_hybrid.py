import sys
import os
import json
import requests

sys.path.append(os.getcwd())

from src.data_acquisition.browser_scraper import (
    to_protobuf_url,
    ProtobufEnum,
    parse_photometa_response
)

panoid = "zpVIs8QgJa887h8HqCBIXw"

# Build request with es and MX in protobuf
toggles = [ProtobufEnum(1), ProtobufEnum(2), ProtobufEnum(3), ProtobufEnum(4), ProtobufEnum(5), ProtobufEnum(6), ProtobufEnum(8), ProtobufEnum(12)]
pano_request_message = {
    1: {1: 'maps_sv.tactile', 11: {2: {1: True}}},
    2: {1: "es", 2: "MX"}, # Standard 2-letter uppercase ISO codes!
    3: {1: {1: ProtobufEnum(2), 2: panoid}},
    4: {
        1: toggles,
        2: {1: ProtobufEnum(1)},
        4: {1: 48},
        5: [{}],
        6: [{}],
        9: {
            1: [
                {1: ProtobufEnum(2), 2: True, 3: ProtobufEnum(2)},
                {1: ProtobufEnum(2), 2: False, 3: ProtobufEnum(3)},
                {1: ProtobufEnum(3), 2: True, 3: ProtobufEnum(2)},
                {1: ProtobufEnum(3), 2: False, 3: ProtobufEnum(3)},
                {1: ProtobufEnum(8), 2: False, 3: ProtobufEnum(3)},
                {1: ProtobufEnum(1), 2: False, 3: ProtobufEnum(3)},
                {1: ProtobufEnum(4), 2: False, 3: ProtobufEnum(3)},
                {1: ProtobufEnum(10), 2: True, 3: ProtobufEnum(2)},
                {1: ProtobufEnum(10), 2: False, 3: ProtobufEnum(3)}
            ]
        },
        11: {
            3: {4: True}
        }
    }
}

# Generate pb
pb_str = to_protobuf_url(pano_request_message)

# Force exact hl=es-419 & gl=mx in the query params!
url = f"https://www.google.com/maps/photometa/v1?authuser=0&hl=es-419&gl=mx&pb={pb_str}"

headers = {
    "Referer": "https://www.google.com/maps/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print(f"URL: {url}")
resp = requests.get(url, headers=headers, timeout=10)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text[:300]}")

try:
    data = json.loads(resp.text[4:])
    meta = parse_photometa_response(data)
    print(f"Parsed meta successfully? {meta is not None}")
    if meta:
        print(json.dumps(meta, indent=2))
except Exception as e:
    print(f"Parsing failed: {e}")
