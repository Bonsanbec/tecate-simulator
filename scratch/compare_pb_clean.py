import sys
import os
from enum import Enum

class SlProtobufType(Enum):
    MESSAGE = "m"
    BOOL = "b"
    DOUBLE = "d"
    ENUM = "e"
    INT = "i"
    STRING = "s"

class SlProtobufEnum:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"ProtobufEnum({str(self.value)})"
    def __str__(self):
        return f"ProtobufEnum({str(self.value)})"

def sl_to_protobuf_url(fields):
    return _sl_to_protobuf_url(fields)[1]

def _sl_to_protobuf_url(fields):
    serialized = ""
    child_count = 0
    for field in fields.items():
        tag = field[0]
        value = field[1]
        sub_child_count, sub_serialized = _sl_field_to_string(tag, value)
        serialized += sub_serialized
        child_count += sub_child_count
    return child_count, serialized

def _sl_message_to_string(tag, value):
    sub_child_count, sub_serialized = _sl_to_protobuf_url(value)
    serialized = f"!{tag}m{sub_child_count}" + sub_serialized
    return sub_child_count + 1, serialized

def _sl_list_to_string(tag, value):
    serialized = ""
    child_count = 0
    for entry in value:
        sub_child_count, sub_serialized = _sl_field_to_string(tag, entry)
        serialized += sub_serialized
        child_count += sub_child_count
    return child_count, serialized

def _sl_field_to_string(tag, value):
    if isinstance(value, list):
        return _sl_list_to_string(tag, value)
    else:
        datatype = _sl_get_datatype_str(value)
        if datatype is SlProtobufType.MESSAGE:
            return _sl_message_to_string(tag, value)
        elif datatype is SlProtobufType.BOOL:
            value = 1 if value else 0
        elif datatype is SlProtobufType.ENUM:
            value = value.value
        return 1, f"!{tag}{datatype.value}{value}"

def _sl_get_datatype_str(value):
    from decimal import Decimal
    if isinstance(value, str):
        datatype = SlProtobufType.STRING
    elif isinstance(value, bool):
        datatype = SlProtobufType.BOOL
    elif isinstance(value, SlProtobufEnum):
        datatype = SlProtobufType.ENUM
    elif isinstance(value, int):
        datatype = SlProtobufType.INT
    elif isinstance(value, float):
        datatype = SlProtobufType.DOUBLE
    elif isinstance(value, Decimal):
        datatype = SlProtobufType.DOUBLE
    elif isinstance(value, dict):
        datatype = SlProtobufType.MESSAGE
    else:
        raise NotImplementedError(value)
    return datatype

def sl_build_find_panorama_by_id_request_url(panoid, download_depth, locale):
    is_ari = len(panoid) != 22
    pano_type = 10 if is_ari else 2
    toggles = []
    include_resolution_info = True
    include_street_name_and_date = True
    include_copyright_information = True
    include_neighbors_and_historical = True
    include_places = True
    include_street_labels = True
    ietf_lang = "en"
    ietf_country = "US"

    toggles.append(SlProtobufEnum(1))
    toggles.append(SlProtobufEnum(2))
    toggles.append(SlProtobufEnum(3))
    toggles.append(SlProtobufEnum(4))
    toggles.append(SlProtobufEnum(5))
    toggles.append(SlProtobufEnum(6))
    toggles.append(SlProtobufEnum(8))
    toggles.append(SlProtobufEnum(12))

    depth1 = [{}]
    depth2 = [{}]

    pano_request_message = {
        1: {1: 'maps_sv.tactile', 11: {2: {1: True}}},
        2: {1: ietf_lang, 2: ietf_country},
        3: {1: {1: SlProtobufEnum(pano_type), 2: panoid}},
        4: {
            1: toggles,
            2: {1: SlProtobufEnum(1)},
            4: {1: 48},
            5: depth1,
            6: depth2,
            9: {
                1: [
                    {1: SlProtobufEnum(2), 2: True, 3: SlProtobufEnum(2)},
                    {1: SlProtobufEnum(2), 2: False, 3: SlProtobufEnum(3)},
                    {1: SlProtobufEnum(3), 2: True, 3: SlProtobufEnum(2)},
                    {1: SlProtobufEnum(3), 2: False, 3: SlProtobufEnum(3)},
                    {1: SlProtobufEnum(8), 2: False, 3: SlProtobufEnum(3)},
                    {1: SlProtobufEnum(1), 2: False, 3: SlProtobufEnum(3)},
                    {1: SlProtobufEnum(4), 2: False, 3: SlProtobufEnum(3)},
                    {1: SlProtobufEnum(10), 2: True, 3: SlProtobufEnum(2)},
                    {1: SlProtobufEnum(10), 2: False, 3: SlProtobufEnum(3)}
                ]
            },
            11: {
                3: {4: True}
            }
        }
    }
    url = f"https://www.google.com/maps/photometa/v1?authuser=0&hl={ietf_lang}&gl={ietf_country}&pb=" \
          + sl_to_protobuf_url(pano_request_message)

    return url

# Now import ours
sys.path.append(os.getcwd())
from src.data_acquisition.browser_scraper import build_find_panorama_by_id_request_url as our_build

panoid = "Qj5sMj8OxrGksOMra1DK1A"

sl_url = sl_build_find_panorama_by_id_request_url(panoid, False, "en-US")
our_url = our_build(panoid, locale="en-US")

print(f"SL URL:\n{sl_url}")
print(f"\nOUR URL:\n{our_url}")
print(f"\nIdentical? {sl_url == our_url}")
