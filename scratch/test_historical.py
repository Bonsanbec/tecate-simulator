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

panoid = "YqZ655EaY28-bpxFBEMLXw"

for p_type in [2, 10]:
    toggles = [ProtobufEnum(1), ProtobufEnum(2), ProtobufEnum(3), ProtobufEnum(4), ProtobufEnum(5), ProtobufEnum(6), ProtobufEnum(8), ProtobufEnum(12)]
    pano_request_message = {
        1: {1: 'maps_sv.tactile', 11: {2: {1: True}}},
        2: {1: "es", 2: "MX"},
        3: {1: {1: ProtobufEnum(p_type), 2: panoid}},
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
    
    url = f"https://www.google.com/maps/photometa/v1?authuser=0&hl=es-419&gl=mx&pb=" + to_protobuf_url(pano_request_message)
    resp = requests.get(url, timeout=10)
    print(f"\n--- TESTING pano_type = {p_type} for {panoid} ---")
    print(f"URL: {url}")
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text[:300].strip()}")
    
    try:
        data = json.loads(resp.text[4:])
        meta = parse_photometa_response(data)
        print(f"Parsed meta successfully? {meta is not None}")
    except Exception as e:
        print(f"Error parsing: {e}")
