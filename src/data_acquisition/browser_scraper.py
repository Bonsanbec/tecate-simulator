import os
import json
import math
import time
import re
import urllib.parse
import requests
from PIL import Image
from io import BytesIO
from enum import Enum
from decimal import Decimal
from datetime import datetime, timezone
from src.core_io.coords import gps_to_local

# Bounding Box Limits for Tecate, Mexico
BBOX_SW_LAT = 32.521704
BBOX_SW_LON = -116.681499
BBOX_NE_LAT = 32.580233
BBOX_NE_LON = -116.510525

# Priority Center: Parque Hidalgo
PARQUE_HIDALGO_LAT = 32.573229
PARQUE_HIDALGO_LON = -116.626536

class ProtobufType(Enum):
    MESSAGE = "m"
    BOOL = "b"
    DOUBLE = "d"
    ENUM = "e"
    INT = "i"
    STRING = "s"

class ProtobufEnum:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"ProtobufEnum({str(self.value)})"
    def __str__(self):
        return f"ProtobufEnum({str(self.value)})"

def to_protobuf_url(fields):
    return _to_protobuf_url(fields)[1]

def _to_protobuf_url(fields):
    serialized = ""
    child_count = 0
    for field in fields.items():
        tag = field[0]
        value = field[1]
        sub_child_count, sub_serialized = _field_to_string(tag, value)
        serialized += sub_serialized
        child_count += sub_child_count
    return child_count, serialized

def _message_to_string(tag, value):
    sub_child_count, sub_serialized = _to_protobuf_url(value)
    serialized = f"!{tag}m{sub_child_count}" + sub_serialized
    return sub_child_count + 1, serialized

def _list_to_string(tag, value):
    serialized = ""
    child_count = 0
    for entry in value:
        sub_child_count, sub_serialized = _field_to_string(tag, entry)
        serialized += sub_serialized
        child_count += sub_child_count
    return child_count, serialized

def _field_to_string(tag, value):
    if isinstance(value, list):
        return _list_to_string(tag, value)
    else:
        datatype = _get_datatype_str(value)
        if datatype is ProtobufType.MESSAGE:
            return _message_to_string(tag, value)
        elif datatype is ProtobufType.BOOL:
            value = 1 if value else 0
        elif datatype is ProtobufType.ENUM:
            value = value.value
        return 1, f"!{tag}{datatype.value}{value}"

def _get_datatype_str(value):
    if isinstance(value, str):
        datatype = ProtobufType.STRING
    elif isinstance(value, bool):
        datatype = ProtobufType.BOOL
    elif isinstance(value, ProtobufEnum):
        datatype = ProtobufType.ENUM
    elif isinstance(value, int):
        datatype = ProtobufType.INT
    elif isinstance(value, float):
        datatype = ProtobufType.DOUBLE
    elif isinstance(value, Decimal):
        datatype = ProtobufType.DOUBLE
    elif isinstance(value, dict):
        datatype = ProtobufType.MESSAGE
    else:
        raise NotImplementedError(value)
    return datatype

def build_find_panorama_by_id_request_url(panoid, download_depth=False, locale="es-MX"):
    is_ari = len(panoid) != 22
    pano_type = 10 if is_ari else 2
    toggles = []
    include_resolution_info = True
    include_street_name_and_date = True
    include_copyright_information = True
    include_neighbors_and_historical = True
    include_places = True
    include_street_labels = True
    
    if locale in ["es-MX", "es-419"]:
        ietf_lang = "es"
        ietf_country = "MX"
        query_lang = "es-419"
        query_country = "mx"
    else:
        parts = locale.split("-")
        ietf_lang = parts[0]
        ietf_country = parts[1].upper() if len(parts) > 1 else parts[0].upper()
        if ietf_lang == "en" and ietf_country == "EN":
            ietf_country = "US"
        query_lang = ietf_lang
        query_country = ietf_country.lower()

    if include_resolution_info:
        toggles.append(ProtobufEnum(1))
    if include_street_name_and_date:
        toggles.append(ProtobufEnum(2))
    if include_copyright_information:
        toggles.append(ProtobufEnum(3))
    toggles.append(ProtobufEnum(4))
    if include_places:
        toggles.append(ProtobufEnum(5))
    if include_neighbors_and_historical:
        toggles.append(ProtobufEnum(6))
    if include_street_labels:
        toggles.append(ProtobufEnum(8))
    toggles.append(ProtobufEnum(12))

    if download_depth:
        depth1 = [{1: ProtobufEnum(1)}, {1: ProtobufEnum(2)}]
        depth2 = [{1: ProtobufEnum(1)}, {1: ProtobufEnum(2)}]
    else:
        depth1 = [{}]
        depth2 = [{}]

    pano_request_message = {
        1: {1: 'maps_sv.tactile', 11: {2: {1: True}}},
        2: {1: ietf_lang, 2: ietf_country},
        3: {1: {1: ProtobufEnum(pano_type), 2: panoid}},
        4: {
            1: toggles,
            2: {1: ProtobufEnum(1)},
            4: {1: 48},
            5: depth1,
            6: depth2,
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
    url = f"https://www.google.com/maps/photometa/v1?authuser=0&hl={query_lang}&gl={query_country}&pb=" \
          + to_protobuf_url(pano_request_message)

    return url

def build_find_panorama_request_url(lat, lon, radius=50, download_depth=False, locale="es-MX", search_third_party=False):
    radius = float(radius)
    toggles = []
    include_resolution_info = True
    include_street_name_and_date = True
    include_copyright_information = True
    include_neighbors_and_historical = True
    
    if locale in ["es-MX", "es-419"]:
        ietf_lang = "es"
        ietf_country = "MX"
    else:
        parts = locale.split("-")
        ietf_lang = parts[0]
        ietf_country = parts[1].upper() if len(parts) > 1 else parts[0].upper()
        if ietf_lang == "en" and ietf_country == "EN":
            ietf_country = "US"

    image_type = 10 if search_third_party else 2

    if download_depth:
        depth1 = {1: ProtobufEnum(0)}
        depth2 = {1: ProtobufEnum(2)}
    else:
        depth1 = {}
        depth2 = {}

    if include_resolution_info:
        toggles.append(ProtobufEnum(1))
    if include_street_name_and_date:
        toggles.append(ProtobufEnum(2))
    if include_copyright_information:
        toggles.append(ProtobufEnum(3))
    toggles.append(ProtobufEnum(4))
    if include_neighbors_and_historical:
        toggles.append(ProtobufEnum(6))
    toggles.append(ProtobufEnum(8))
    toggles.append(ProtobufEnum(12))

    search_message = {
        1: {
            1: 'apiv3',
            5: 'US',
            11: {1: {1: False}}
        },
        2: {1: {3: lat, 4: lon}, 2: radius},
        3: {
            2: {1: ietf_lang, 2: ietf_country},
            9: {1: ProtobufEnum(2)},
            11: {
                1: {1: ProtobufEnum(image_type), 2: True, 3: ProtobufEnum(2)}
            },
        },
        4: {
            1: toggles,
            5: depth1,
            6: depth2,
        }
    }

    url = "https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=" \
          + to_protobuf_url(search_message) + "&callback=_xdc_._v2mub5"
          
    return url

def repair_find_panorama_response(text):
    try:
        first_paren = text.index("(")
        last_paren = text.rindex(")")
        return "[" + text[first_paren + 1:last_paren] + "]"
    except Exception:
        return text

def parse_photometa_response(data: dict) -> dict | None:
    msg = None
    try:
        if data[1][0][0][0] == 1:
            msg = data[1][0]
    except Exception:
        pass
        
    if msg is None:
        try:
            if data[0][0][0] == 0:
                msg = data[0][1]
        except Exception:
            pass
            
    if msg is None:
        return None
        
    try:
        panoid = msg[1][1]
        
        # Latitude / Longitude
        lat = float(msg[5][0][1][0][2])
        lon = float(msg[5][0][1][0][3])
        
        # Date
        date_str = ""
        try:
            date_list = msg[6][7]
            if date_list:
                date_str = f"{date_list[0]}-{date_list[1]:02d}"
        except Exception:
            pass
            
        if not date_str:
            try:
                if msg[12] and msg[12][0] != "":
                    parts = msg[12][0].split("/")
                    if len(parts) >= 2:
                        timestamp = int(parts[1]) / 1000
                        dt = datetime.fromtimestamp(timestamp, timezone.utc)
                        date_str = f"{dt.year}-{dt.month:02d}"
            except Exception:
                pass
                
        # Road name
        road_name = ""
        try:
            road_name = msg[5][0][12][0][0][0][2][0]
        except Exception:
            try:
                road_name = msg[3][2][0][0]
            except Exception:
                pass
                
        # Adjacent links and timeline
        links_dict = {}
        try:
            links_raw = msg[5][0][6]
            if links_raw:
                links_dict = dict([(x[0], x[1] if len(x) > 1 else None) for x in links_raw])
        except Exception:
            pass
            
        timeline_dict = {}
        try:
            other_dates_raw = msg[5][0][8]
            if other_dates_raw:
                timeline_dict = dict([(x[0], x[1]) for x in other_dates_raw])
        except Exception:
            pass
            
        adjacent_links = []
        timeline = []
        
        try:
            others = msg[5][0][3][0]
            if others:
                for idx, other in enumerate(others):
                    other_id = other[0][1]
                    if other_id == panoid:
                        continue
                        
                    if idx in timeline_dict:
                        tl_date_list = timeline_dict[idx]
                        tl_date_str = ""
                        if tl_date_list:
                            tl_date_str = f"{tl_date_list[0]}-{tl_date_list[1]:02d}"
                        timeline.append({
                            "pano_id": other_id,
                            "date": tl_date_str
                        })
                    elif idx in links_dict:
                        yaw_val = 0.0
                        try:
                            yaw_val = float(links_dict[idx][3])
                        except Exception:
                            try:
                                yaw_val = float(other[2][2][0])
                            except Exception:
                                pass
                        
                        other_road = ""
                        try:
                            other_road = other[3][2][0][0]
                        except Exception:
                            pass
                            
                        adjacent_links.append({
                            "pano_id": other_id,
                            "road_name": other_road,
                            "yaw_deg": yaw_val
                        })
        except Exception:
            pass
            
        # Parse projection pitch, roll, yaw, and altitude from msg[5][0][1]
        altitude_val = 0.0
        pitch_val = 0.0
        roll_val = 0.0
        proj_yaw_val = None
        
        try:
            p_block = msg[5][0][1]
            if len(p_block) >= 3:
                # Altitude is at index 1
                if p_block[1] and len(p_block[1]) > 0:
                    altitude_val = float(p_block[1][0])
                
                # Projection yaw, pitch, roll are at index 2
                if p_block[2] and len(p_block[2]) >= 3:
                    pitch_val = float(p_block[2][0])
                    proj_yaw_val = float(p_block[2][1])
                    raw_roll = float(p_block[2][2])
                    # Normalize roll to [-180.0, 180.0]
                    roll_val = (raw_roll + 180.0) % 360.0 - 180.0
        except Exception:
            pass

        return {
            "pano_id": panoid,
            "latitude": lat,
            "longitude": lon,
            "altitude": altitude_val,
            "pitch": pitch_val,
            "roll": roll_val,
            "projection_yaw": proj_yaw_val,
            "date": date_str,
            "road_name": road_name,
            "adjacent_links": adjacent_links,
            "timeline": timeline
        }
    except Exception as e:
        print(f"[Photometa Parse Error] Failed to parse message: {e}")
        return None

class GoogleStreetViewScraper:
    """
    Reverse-engineered, Chromium-driven historical Street View screenshot harvester.
    Queries unauthenticated public metadata services to resolve coordinates and circa-2009 timeline states,
    navigates a persistent Chromium browser to clean perspective views, and captures high-resolution screenshots.
    """
    def __init__(self, headless: bool = True, log: bool = False, G = None):
        self.headless = headless
        self.log = log
        self.G = G
        
        # Persistent Playwright browser session variables
        self.playwright = None
        self.playwright_context_manager = None
        self.browser = None
        self.context = None
        self.page = None
        self.intercepted_panos = {}

    def __del__(self):
        self.close()

    def init_browser(self):
        """Initializes a persistent Chromium session if not already running."""
        if self.browser is not None:
            return
        
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[Warning] Playwright not found. Browser session cannot be initialized.")
            return

        print("[Playwright] Booting persistent Chromium instance...")
        self.playwright_context_manager = sync_playwright()
        self.playwright = self.playwright_context_manager.__enter__()
        
        try:
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--use-gl=angle",
                    "--use-angle=swiftshader",
                    "--ignore-gpu-blocklist",
                    "--disable-web-security"
                ]
            )
        except Exception as e:
            print("\n" + "="*80)
            print(f"[Error] Playwright failed to launch the Chromium browser: {e}")
            
            # Detect platform & print help
            import sys
            is_linux = sys.platform.startswith("linux")
            is_wsl_env = False
            if is_linux:
                try:
                    with open("/proc/version", "r") as f:
                        content = f.read().lower()
                        is_wsl_env = "microsoft" in content or "wsl" in content
                except Exception:
                    pass
            
            if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
                print("\nMissing Playwright browser binaries!")
                print("To install, run:")
                print("    playwright install chromium")
                print("Or if using virtualenv:")
                print("    ./venv/bin/playwright install chromium")
            elif is_linux:
                print("\nMissing system libraries for Chromium on Linux/WSL!")
                print("To install the required dependencies, run:")
                print("    playwright install-deps")
                print("Or if using virtualenv:")
                print("    ./venv/bin/playwright install-deps")
                if is_wsl_env and not self.headless:
                    print("\nTip: WSL does not have a display server by default. Ensure you run with --headless.")
            print("="*80 + "\n")
            raise e
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        
        os.makedirs("data/screenshots", exist_ok=True)
        self.intercepted_panos = {}
        print("[Playwright] Persistent Chromium session initialized.")

    def close(self):
        """Safely closes the persistent Chromium instance."""
        if self.browser:
            print("[Playwright] Closing persistent Chromium instance...")
            try:
                self.browser.close()
            except Exception as e:
                print(f"[Warning] Error closing browser: {e}")
            self.browser = None
        if self.playwright:
            try:
                self.playwright_context_manager.__exit__(None, None, None)
            except Exception as e:
                print(f"[Warning] Error exiting playwright manager: {e}")
            self.playwright = None
        self.context = None
        self.page = None

    def capture_facade_screenshot(self, lat: float, lon: float, heading: float, pano_id: str, slice_id: str = "debug") -> bytes | None:
        """
        Navigates the persistent browser directly to the street view URL at the target pano_id,
        oriented orthogonally at the building facade (heading) with pitch 0 and field of view 60.
        Injects CSS to hide Google Maps UI overlays, waits 5.0 seconds for WebGL tiles to load,
        takes a screenshot of the clean WebGL view, and returns the screenshot bytes.
        """
        self.init_browser()
        if not self.page:
            print("[Warning] Browser page could not be initialized.")
            return None

        # Build classic direct Street View URL with pitch=0
        url = f"https://www.google.com/maps?layer=c&cbll={lat},{lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0"
        print(f"[Playwright] Capturing facade slice [{slice_id}] at heading {heading:.1f} via URL: {url}")

        try:
            self.page.goto(url, wait_until="load", timeout=35000)
            
            # Wait for the main canvas element to be visible
            self.page.wait_for_selector("canvas", timeout=15000)
            
            # Inject CSS to hide all Google Maps overlays completely (test_perfect_hide.py approach)
            self.page.evaluate("""
                () => {
                    const style = document.createElement('style');
                    style.id = 'clean-streetview-style';
                    style.textContent = `
                        .Owrmqf, .C5SiJf, .fBpDtb, .b3vVFf, .TorxFf, .PlF8V, .F63Kk, .bqcX3e, .EtdG7d, .e9Chtd,
                        .noprint, .gmnoprint, .gm-style-cc,
                        [class*="place-card"], #titlecard,
                        #minimap, [class*="minimap"],
                        #layers-menu, #compass, #widget-zoom,
                        #watermark, [class*="watermark"],
                        button[aria-label*="Back"], .gm-control-active,
                        [aria-label*="Back to map"], [class*="watermark"] {
                            display: none !important;
                        }
                    `;
                    document.head.append(style);
                }
            """)
            
            # Wait for WebGL tiles to stabilize and render in high-res
            try:
                self.page.wait_for_load_state("networkidle", timeout=1500)
            except Exception:
                pass
            time.sleep(1.0) # Short stabilization sleep instead of fixed 5.0s
            
            # Capture viewport screenshot
            screenshot_bytes = self.page.screenshot()
            
            # Save a debug screenshot for visual diagnostic confirmation (avoided for temp_ captures)
            if not slice_id.startswith("temp_"):
                os.makedirs("data/screenshots/facades", exist_ok=True)
                debug_path = f"data/screenshots/facades/{slice_id}.png"
                with open(debug_path, "wb") as f:
                    f.write(screenshot_bytes)
                
            return screenshot_bytes
        except Exception as e:
            print(f"[Warning] Failed to capture facade screenshot for slice {slice_id}: {e}")
            return None

    def fetch_public_metadata(self, lat: float = None, lon: float = None, pano_id: str = None, locale: str = "es-MX") -> dict | None:
        """
        Queries Google's unauthenticated client backend endpoint to reverse-engineer 
        coordinates, date parameters, road labels, timeline listings, and graph links.
        Supports both the modern unauthenticated photometa API and legacy CBK mocks for tests.
        """
        if pano_id:
            url = build_find_panorama_by_id_request_url(pano_id, locale=locale)
        elif lat is not None and lon is not None:
            url = build_find_panorama_request_url(lat, lon, locale=locale)
        else:
            return None
            
        try:
            if (self.log):
                print(f"[fetch_public_metadata Debug] Querying URL: {url}")
            headers = {
                "Referer": "https://www.google.com/maps/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
                
            if (self.log):    
                print(f"[fetch_public_metadata Debug] Response Status: {resp.status_code}")
                print(f"[fetch_public_metadata Debug] Response Text (first 100 chars): {resp.text[:100].strip()}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict) and "Location" in data:
                        loc = data["Location"]
                        p_id = loc.get("panoId")
                        
                        links = []
                        for l in data.get("Annotation", {}).get("Link", []):
                            links.append({
                                "pano_id": l.get("panoId"),
                                "road_name": l.get("road_name", ""),
                                "yaw_deg": float(l.get("yawDeg", None))
                            })
                            
                        timeline = []
                        for old in data.get("Links", []):
                            timeline.append({
                                "pano_id": old.get("panoId"),
                                "date": old.get("date", "")
                            })
                            
                        meta = {
                            "pano_id": p_id,
                            "latitude": float(loc.get("latitude", lat)),
                            "longitude": float(loc.get("longitude", lon)),
                            "date": data.get("Data", {}).get("image_date", ""),
                            "road_name": loc.get("road_name", ""),
                            "adjacent_links": links,
                            "timeline": timeline
                        }
                        
                        if meta["latitude"] is None or meta["longitude"] is None:
                            print("⚠️ [WARNING] Skipping null lat/long meta!")
                            return None
                        
                        return meta
                except Exception:
                    pass

                text = resp.text
                if pano_id:
                    data = json.loads(text[4:])
                else:
                    json_str = repair_find_panorama_response(text)
                    data = json.loads(json_str)
                    
                meta = parse_photometa_response(data)
                if meta:
                    if lat is not None and meta.get("latitude") is None:
                        meta["latitude"] = lat
                    if lon is not None and meta.get("longitude") is None:
                        meta["longitude"] = lon
                return meta
                
            return None
        except Exception as e:
            try:
                data = resp.json()
                if isinstance(data, dict) and "Location" in data:
                    loc = data["Location"]
                    p_id = loc.get("panoId")
                    links = []
                    for l in data.get("Annotation", {}).get("Link", []):
                        links.append({
                            "pano_id": l.get("panoId"),
                            "road_name": l.get("road_name", ""),
                            "yaw_deg": float(l.get("yawDeg", 0.0))
                        })
                    timeline = []
                    for old in data.get("Links", []):
                        timeline.append({
                            "pano_id": old.get("panoId"),
                            "date": old.get("date", "")
                        })
                    meta = {
                        "pano_id": p_id,
                        "latitude": float(loc.get("latitude", lat)),
                        "longitude": float(loc.get("longitude", lon)),
                        "date": data.get("Data", {}).get("image_date", ""),
                        "road_name": loc.get("road_name", ""),
                        "adjacent_links": links,
                        "timeline": timeline
                    }
                    
                    if meta["latitude"] is None or meta["longitude"] is None:
                            print("⚠️ [WARNING] Skipping null lat/long meta!")
                            return None
                        
                    return meta
            except Exception:
                pass
            print(f"[fetch_public_metadata Error] {e}")
            return None
