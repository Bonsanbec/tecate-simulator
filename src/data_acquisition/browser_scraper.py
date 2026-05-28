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
            
        return {
            "pano_id": panoid,
            "latitude": lat,
            "longitude": lon,
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
    Reverse-engineered, Chromium-driven historical Street View crawler.
    Traverses the real public Google Maps Street View graph, detects timeline revisions,
    extracts the oldest captures, enforces Parque Hidalgo spatial priority queues,
    checks bounding boxes, and persists crash-resilient states locally.
    """
    def __init__(self, cache_dir: str = "data/raw_scraped", headless: bool = True):
        self.cache_dir = cache_dir
        self.headless = headless
        self.state_file = "data/scraper_state.json"
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Persistent Playwright browser session variables
        self.playwright = None
        self.playwright_context_manager = None
        self.browser = None
        self.context = None
        self.page = None
        self.intercepted_panos = {}
        
        # Load incremental persistence memory
        self.load_state()

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
        
        # Enable chrome arguments for smooth WebGL support and standard user agent
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--ignore-gpu-blocklist",
                "--disable-web-security"
            ]
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        
        # Directory for debug screenshots
        os.makedirs("data/screenshots", exist_ok=True)
        
        # Listen to background XHR / tile network responses to parse panoId in memory
        self.intercepted_panos = {}
        def intercept_response(response):
            try:
                r_url = response.url
                if "output=tile" in r_url or "/v1/tile" in r_url:
                    parsed = urllib.parse.urlparse(r_url)
                    params = urllib.parse.parse_qs(parsed.query)
                    p_id = params.get("panoid", [None])[0]
                    if p_id:
                        self.intercepted_panos[p_id] = time.time()
                        
                # Check cbk metadata responses
                if "cbk?output=json" in r_url or "cbk" in r_url:
                    text = response.text()
                    if "panoId" in text:
                        match = re.search(r'"panoId"\s*:\s*"([a-zA-Z0-9_\-]{22})"', text)
                        if match:
                            self.intercepted_panos[match.group(1)] = time.time()
            except Exception:
                pass

        self.page.on("response", intercept_response)
        print("[Playwright] Persistent Chromium session initialized and network listener registered.")

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

    def load_state(self):
        """Loads persistent crawler memory from disk, ensuring resilience against crashes."""
        if os.path.exists(self.state_file):
            print(f"[Scraper Memory] Resuming crawl from existing state file: {self.state_file}")
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self.visited_panos = set(state.get("visited_panos", []))
                self.crawl_queue = state.get("crawl_queue", [])
                self.failed_panos = state.get("failed_panos", {})
                self.road_graph = state.get("road_graph", [])
                self.resolved_seed_coordinate = state.get("resolved_seed_coordinate", None)
                print(f"[Scraper Memory] State loaded: {len(self.visited_panos)} crawled nodes, {len(self.crawl_queue)} queued nodes.")
                return
            except Exception as e:
                print(f"[Scraper Memory] Failed to parse state: {e}. Reinitializing.")
                
        # Fresh initialization
        self.visited_panos = set()
        self.crawl_queue = []
        self.failed_panos = {}
        self.road_graph = []
        self.resolved_seed_coordinate = None

    def save_state(self):
        """Saves current traversal state to disk to survive crashes and restarts."""
        state = {
            "visited_panos": list(self.visited_panos),
            "crawl_queue": self.crawl_queue,
            "failed_panos": self.failed_panos,
            "road_graph": self.road_graph,
            "resolved_seed_coordinate": self.resolved_seed_coordinate
        }
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            print(f"[Scraper Memory] Failed to save state file: {e}")

    def is_within_bbox(self, lat: float, lon: float) -> bool:
        """Enforces Bounding Box coordinates limit."""
        return (BBOX_SW_LAT <= lat <= BBOX_NE_LAT) and (BBOX_SW_LON <= lon <= BBOX_NE_LON)

    def calculate_distance_to_parque_hidalgo(self, lat: float, lon: float) -> float:
        """Computes Euclidean distance in degrees to Parque Hidalgo for spatial priority weightings."""
        return math.sqrt((lat - PARQUE_HIDALGO_LAT)**2 + (lon - PARQUE_HIDALGO_LON)**2)

    def generate_spiral_offsets(self):
        """Generates expanding coordinate spiral grid search offsets to perturb coordinates on seed failures."""
        dx, dy = 0, -1
        x, y = 0, 0
        for step in range(1, 100):
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                dx, dy = -dy, dx  # Turn 90 degrees
            x, y = x + dx, y + dy
            # Spacing of 0.00015 degrees (approx 16 meters)
            yield x * 0.00015, y * 0.00015

    def run_browser_session_and_intercept(self, lat: float, lon: float) -> str | None:
        """
        Launches or reuses a persistent Playwright Chromium session, navigates
        to the target coordinates in normal map mode, stabilizes the map,
        programmatically triggers Street View using the Pegman control, drops
        Pegman at the target center, and resolves the actual pano ID.
        """
        self.init_browser()
        if not self.page:
            print("[Warning] Browser page could not be initialized.")
            return None

        # 1. Normal Map Mode Bootstrapping
        url = f"https://www.google.com/maps/@{lat},{lon},18z"
        print(f"\n[Playwright] Bootstrapping from normal map mode at coordinates: {url}")
        
        try:
            # Navigate to standard map mode
            self.page.goto(url, wait_until="load", timeout=35000)
            
            # Wait for stabilization (essential to let zoom/pegman overlays load)
            print("[Playwright] Waiting 5.0 seconds for UI overlays and Pegman controls to stabilize...")
            time.sleep(5.0)
            
            # Wait for map canvas/stabilization
            try:
                self.page.wait_for_selector("canvas", timeout=15000)
                print("[Playwright] Normal map canvas detected and stabilized.")
            except Exception as e:
                print(f"[Warning] Map canvas selector timeout: {e}")
            
            # Take standard map loaded screenshot
            screenshot_path = f"data/screenshots/01_map_loaded_{lat:.6f}_{lon:.6f}.png"
            self.page.screenshot(path=screenshot_path)
            print(f"[Playwright Debug] Standard map loaded screenshot saved to: {screenshot_path}")

            # 2. Locate Pegman / Street View control using resilient selectors
            pegman_btn = None
            selectors = [
                ".sHj5c.a8QCmb",  # Language-agnostic Pegman button class!
                "button[aria-label*='Street View']",
                "button[aria-label*='Pegman']",
                "button[aria-label*='imágenes de Street View']",
                "button[aria-label*='imágenes']",
                "button[aria-label*='street view']",
                "button[aria-label*='pegman']",
                "[aria-label*='Street View']",
                "[aria-label*='Pegman']",
                ".gm-svpc",
                "[class*='pegman']",
                "button:has(img[src*='pegman'])"
            ]
            
            for selector in selectors:
                try:
                    loc = self.page.locator(selector).first
                    loc.wait_for(state="visible", timeout=3000)
                    pegman_btn = loc
                    print(f"[Playwright] Found Pegman button using selector: '{selector}'")
                    break
                except Exception:
                    continue
            
            if not pegman_btn:
                print("[Warning] Pegman / Street View button not found in DOM. Attempting fallback clicking/drag-drop...")
                # Let's save a failure screenshot
                self.page.screenshot(path=f"data/screenshots/fail_no_pegman_{lat:.6f}_{lon:.6f}.png")
            
            # 3. Activate Street View mode programmatically
            # Get viewport center coordinates to click or drop pegman
            viewport = self.page.viewport_size or {"width": 1280, "height": 720}
            center_x = viewport["width"] / 2
            center_y = viewport["height"] / 2

            pano_id = None
            
            if pegman_btn:
                # Click pegman button to toggle Street View lines
                try:
                    pegman_btn.click(timeout=5000)
                    print("[Playwright] Clicked Pegman button to activate Street View overlays.")
                    time.sleep(2.0)  # Wait for overlays to draw
                    
                    # Take screenshot after pegman clicked
                    self.page.screenshot(path=f"data/screenshots/02_pegman_active_{lat:.6f}_{lon:.6f}.png")
                    
                    # Click on map canvas offsets in a cross pattern to hit surrounding blue roads
                    # We click road offsets FIRST, and center (park) LAST to avoid triggering place panels early!
                    click_offsets = [
                        (-150, 0),     # Left road (hits Lázaro Cárdenas)
                        (150, 0),      # Right road (hits Ortiz Rubio)
                        (0, -150),     # Top road (hits Tecate - Tijuana highway)
                        (0, 150),      # Bottom road (hits Libertad)
                        (-150, -150),  # Top-Left intersection
                        (150, 150),    # Bottom-Right intersection
                        (0, 0)         # Center fallback (hits Parque Hidalgo)
                    ]
                    
                    for dx, dy in click_offsets:
                        click_x = center_x + dx
                        click_y = center_y + dy
                        print(f"[Playwright] Clicking map at offset ({dx}, {dy}) -> coordinates ({click_x}, {click_y}) to drop Pegman on blue road...")
                        self.page.mouse.click(click_x, click_y)
                        time.sleep(2.5)  # Wait for transition to trigger
                        
                        # Check if Street View resolved
                        current_url = self.page.url
                        window_url = self.page.evaluate("window.location.href")
                        if "!1s" in current_url or "!1s" in window_url or self.intercepted_panos:
                            print(f"[Playwright Success] Street View transition triggered by click at offset ({dx}, {dy})!")
                            break
                        else:
                            # Press Escape to close any accidentally opened details panels or popups
                            print("[Playwright Debug] Dismissing any potential place selection panels via Escape key...")
                            self.page.keyboard.press("Escape")
                            time.sleep(0.5)
                            
                except Exception as e:
                    print(f"[Warning] Failed to programmatically click/interact with Pegman control: {e}")

            # 4. Fallback Drag and Drop Simulation (if click didn't trigger Street View transition)
            # Check if we successfully entered Street View (URL changes to contain !1s...)
            current_url = self.page.url
            if "!1s" not in current_url and "!1s" not in self.page.evaluate("window.location.href") and not self.intercepted_panos:
                print("[Playwright] Click offsets did not trigger Street View. Attempting fallback mouse drag-and-drop...")
                if pegman_btn:
                    box = pegman_btn.bounding_box()
                    if box:
                        try:
                            # Drag to a known road location (e.g. left of center, to hit Lázaro Cárdenas road)
                            target_x = center_x - 150
                            target_y = center_y
                            start_x = box["x"] + box["width"] / 2
                            start_y = box["y"] + box["height"] / 2
                            print(f"[Playwright] Dragging Pegman from ({start_x}, {start_y}) to road target ({target_x}, {target_y})...")
                            self.page.mouse.move(start_x, start_y)
                            self.page.mouse.down()
                            time.sleep(0.5)
                            self.page.mouse.move(target_x, target_y, steps=15)
                            time.sleep(0.5)
                            self.page.mouse.up()
                            time.sleep(4.0)  # Wait for Street View loading to initialize
                        except Exception as drag_err:
                            print(f"[Warning] Drag-and-drop interaction failed: {drag_err}")

            # 5. Monitor and Poll for Panorama Transition & Resolution
            print("[Playwright] Monitoring URL state, background responses, and canvas elements...")
            start_time = time.time()
            
            while time.time() - start_time < 15.0:
                # A. Poll Address Bar URL
                current_url = self.page.url
                match = re.search(r'!1s([a-zA-Z0-9_\-]{20,22})', current_url)
                if match:
                    pano_id = match.group(1)
                    print(f"[Playwright] Successfully resolved pano ID from browser URL: {pano_id}")
                    break

                # B. Poll Window location state
                window_url = self.page.evaluate("window.location.href")
                match_win = re.search(r'!1s([a-zA-Z0-9_\-]{20,22})', window_url)
                if match_win:
                    pano_id = match_win.group(1)
                    print(f"[Playwright] Successfully resolved pano ID from window.location.href: {pano_id}")
                    break

                # C. Check intercepted network panorama IDs
                if self.intercepted_panos:
                    # Pick the most recently intercepted pano ID
                    sorted_panos = sorted(self.intercepted_panos.items(), key=lambda item: item[1], reverse=True)
                    if sorted_panos:
                        pano_id = sorted_panos[0][0]
                        print(f"[Playwright] Resolved pano ID from intercepted tile/metadata requests: {pano_id}")
                        break

                time.sleep(0.5)

            # 6. Validate Street View mode is active & capture success/failure state
            if pano_id:
                # Check for active canvas and navigation UI overlay controls
                canvas_visible = False
                try:
                    canvas_visible = self.page.locator("canvas").first.is_visible(timeout=2000)
                except Exception:
                    pass
                
                print(f"[Playwright] Street View Active Verification: Canvas visible={canvas_visible}")
                
                success_screenshot_path = f"data/screenshots/03_street_view_active_{pano_id}.png"
                self.page.screenshot(path=success_screenshot_path)
                print(f"[Playwright Success] Street View successfully opened! Screenshot saved to: {success_screenshot_path}")
            else:
                fail_screenshot_path = f"data/screenshots/fail_street_view_failed_{lat:.6f}_{lon:.6f}.png"
                self.page.screenshot(path=fail_screenshot_path)
                print(f"[Playwright Warning] Street View transition failed or timed out. Screenshot saved to: {fail_screenshot_path}")

            return pano_id
        except Exception as e:
            print(f"[Warning] Playwright browser session encountered a technical issue: {e}")
            try:
                self.page.screenshot(path=f"data/screenshots/fail_exception_{lat:.6f}_{lon:.6f}.png")
            except Exception:
                pass
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
            use_playwright = False
            response_text_content = None
            status_code = None
            
            if self.page is not None:
                try:
                    print(f"[fetch_public_metadata] Querying URL via active Playwright Chromium session: {url}")
                    response_text = self.page.evaluate(f"""
                        async () => {{
                            try {{
                                const response = await fetch({json.dumps(url)});
                                return {{
                                    status: response.status,
                                    text: await response.text()
                                }};
                            }} catch (err) {{
                                return {{
                                    status: 500,
                                    text: err.toString()
                                }};
                            }}
                        }}
                    """)
                    if response_text and response_text.get("status") == 200:
                        text_val = response_text.get("text")
                        if "[null, 2]" not in text_val:
                            status_code = 200
                            response_text_content = text_val
                            use_playwright = True
                            print(f"[fetch_public_metadata] Playwright Fetch Status: {status_code}")
                        else:
                            print(f"[fetch_public_metadata] Playwright Fetch returned [null, 2]. Falling back to standard requests.")
                except Exception as pe:
                    print(f"[fetch_public_metadata Warning] Playwright fetch failed: {pe}. Falling back to standard requests.")

            print(f"[fetch_public_metadata Debug] Querying URL: {url}")
            if use_playwright:
                class MockResponse:
                    def __init__(self, text, status_code):
                        self.text = text
                        self.status_code = status_code
                    def json(self):
                        return json.loads(self.text)
                resp = MockResponse(response_text_content, status_code)
            else:
                headers = {
                    "Referer": "https://www.google.com/maps/",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                resp = requests.get(url, headers=headers, timeout=10)
                
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
                            "latitude": float(loc.get("latitude", lat if lat is not None else 0.0)),
                            "longitude": float(loc.get("longitude", lon if lon is not None else 0.0)),
                            "date": data.get("Data", {}).get("image_date", ""),
                            "road_name": loc.get("road_name", ""),
                            "adjacent_links": links,
                            "timeline": timeline
                        }
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
                        "latitude": float(loc.get("latitude", lat if lat is not None else 0.0)),
                        "longitude": float(loc.get("longitude", lon if lon is not None else 0.0)),
                        "date": data.get("Data", {}).get("image_date", ""),
                        "road_name": loc.get("road_name", ""),
                        "adjacent_links": links,
                        "timeline": timeline
                    }
                    return meta
            except Exception:
                pass
            print(f"[fetch_public_metadata Error] {e}")
            return None

    def download_and_stitch_tiles(self, pano_id: str, zoom: int = 3, allow_synthetic: bool = False) -> Image.Image | None:
        """
        Downloads cubic projection tiles directly from public servers, stitches them,
        crops the facade horizon, and saves the authentic high-resolution equirectangular panorama.
        Strictly disables synthetic fallbacks in real mode if download fails.
        """
        url_template = "https://streetviewpixels-pa.googleapis.com/v1/tile"
        headers = {
            "Referer": "https://www.google.com/maps/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Check if the panorama is modern (8 columns) or legacy (7 columns)
        # We query the 8th column (x=7, y=0) at zoom 3. If it returns 400/404, we know this is a 7-column legacy panorama!
        cols = 8
        rows = 4
        tile_w = 512
        tile_h = 512

        test_params = {
            "cb_client": "maps_sv.tactile",
            "panoid": pano_id,
            "x": "7",
            "y": "0",
            "zoom": str(zoom),
            "nbt": "1",
            "fover": "2"
        }
        try:
            test_resp = requests.get(url_template, params=test_params, headers=headers, timeout=5)
            if test_resp.status_code in [400, 404]:
                cols = 7
                print(f"[Tile Downloader] Detected legacy panorama format with 7 columns for pano {pano_id}.")
        except Exception:
            pass

        panorama = Image.new("RGB", (cols * tile_w, rows * tile_h))
        downloaded = 0
        
        tile_dir = os.path.join(self.cache_dir, pano_id, "tiles")
        os.makedirs(tile_dir, exist_ok=True)
        
        for y in range(rows):
            for x in range(cols):
                params = {
                    "cb_client": "maps_sv.tactile",
                    "panoid": pano_id,
                    "x": str(x),
                    "y": str(y),
                    "zoom": str(zoom),
                    "nbt": "1",
                    "fover": "2"
                }
                
                tile_path = os.path.join(tile_dir, f"tile_z{zoom}_{x}_{y}.png")
                
                if os.path.exists(tile_path):
                    try:
                        tile_img = Image.open(tile_path)
                        panorama.paste(tile_img, (x * tile_w, y * tile_h))
                        downloaded += 1
                        continue
                    except:
                        pass
                        
                try:
                    resp = requests.get(url_template, params=params, headers=headers, timeout=10)
                    if resp.status_code == 200 and len(resp.content) > 500:
                        tile_img = Image.open(BytesIO(resp.content))
                        tile_img.save(tile_path)  # Save raw tile before stitch
                        panorama.paste(tile_img, (x * tile_w, y * tile_h))
                        downloaded += 1
                        time.sleep(0.15)  # Rate limiting throttle
                except Exception as e:
                    pass
                    
        # Success Condition: must have authentic high-resolution tiles
        if downloaded >= (cols * rows) - 2:
            # Crop horizontal facade band (aspect ratio 4:1)
            facade_strip = panorama.crop((0, 680, cols * tile_w, 1704))
            resized = facade_strip.resize((2560, 640), Image.Resampling.BILINEAR)
            return resized
            
        # In real mode, synthetic fallbacks are strictly prohibited
        if not allow_synthetic:
            print(f"[Crawler Warning] Incomplete authentic tiles captured for node {pano_id}. Synthetic fallback is prohibited.")
            return None
            
        # Simulated fallback (only allowed in synthetic offline mode)
        print(f"[Crawler Simulated Fallback] Generating synthetic facade backdrop for {pano_id}.")
        pano_img = Image.new("RGB", (2560, 640), (135, 206, 235))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(pano_img)
        draw.rectangle([0, 320, 2560, 640], fill=(80, 80, 80))
        draw.rectangle([0, 480, 2560, 520], fill=(150, 150, 150))
        return pano_img

    def queue_node(self, pano_id: str, lat: float, lon: float):
        """Calculates Parque Hidalgo priority weight and queues the node, sorted by proximity."""
        if pano_id in self.visited_panos or any(item["pano_id"] == pano_id for item in self.crawl_queue):
            return
            
        dist = self.calculate_distance_to_parque_hidalgo(lat, lon)
        
        # Priority entry structure
        self.crawl_queue.append({
            "pano_id": pano_id,
            "latitude": lat,
            "longitude": lon,
            "priority_distance": dist
        })
        
        # Sort queue: closest to Parque Hidalgo first (distance ascending)
        self.crawl_queue.sort(key=lambda x: x["priority_distance"])

    def crawl_priority_network(self, seed_lat: float, seed_lon: float, max_nodes: int = 25) -> list[dict]:
        """
        Executes a priority-weighted, crash-resilient graph traversal along real
        Street View segments, strictly bounded inside Tecate and sorted outward from Parque Hidalgo.
        """
        try:
            # Discover initial seed node if queue is empty and we haven't started
            if len(self.crawl_queue) == 0 and len(self.visited_panos) == 0:
                seed_pano = None
                
                # Check cached seed coordinate to bypass slow resolution if restarting
                if self.resolved_seed_coordinate:
                    print(f"[Scraper Memory] Loading successfully resolved seed pano from state: {self.resolved_seed_coordinate}")
                    seed_pano = self.resolved_seed_coordinate
                else:
                    # 1. Asynchronous Panorama Resolution Pipeline
                    print(f"[Scraper] Resolving crawler seed coordinate near Parque Hidalgo ({seed_lat}, {seed_lon})...")
                    seed_pano = self.run_browser_session_and_intercept(seed_lat, seed_lon)
                    
                    # 2. Spiral Search Retry Logic
                    if not seed_pano:
                        print("[Scraper Warning] Initial seed coordinate returned null. Executing expanding spiral search...")
                        offset_gen = self.generate_spiral_offsets()
                        for d_lat, d_lon in offset_gen:
                            p_lat = seed_lat + d_lat
                            p_lon = seed_lon + d_lon
                            print(f"[Spiral Search] Perturbing seed target to offset ({p_lat:.6f}, {p_lon:.6f})...")
                            
                            # Navigate browser and try to resolve panoId
                            seed_pano = self.run_browser_session_and_intercept(p_lat, p_lon)
                            if seed_pano:
                                print(f"[Spiral Search] Successfully resolved seed coordinates at offset! Pano ID: {seed_pano}")
                                self.resolved_seed_coordinate = seed_pano
                                break
                                
                # Direct XHR query to confirm seed node connectivity
                try:
                    seed_meta = self.fetch_public_metadata(lat=seed_lat, lon=seed_lon, pano_id=seed_pano)
                    print(f"[Crawler Debug] Direct XHR seed metadata query returned: {seed_meta}")
                    if not seed_meta and seed_lat is not None and seed_lon is not None:
                        print("[Crawler Debug] Direct XHR seed metadata query returned None. Retrying via coordinate lookup fallback...")
                        seed_meta = self.fetch_public_metadata(lat=seed_lat, lon=seed_lon)
                        print(f"[Crawler Debug] Coordinate lookup fallback returned: {seed_meta}")
                except Exception as e:
                    print(f"[Crawler Debug] Direct XHR seed metadata query raised error: {e}")
                    seed_meta = None
                
                if seed_meta:
                    self.queue_node(seed_meta["pano_id"], seed_meta["latitude"], seed_meta["longitude"])
                    self.save_state()
                else:
                    print("[Warning] Scraper seed coordinate lookup returned null. Aborting crawl.")
                    return []
                    
            crawled_nodes = []
            crawled_count = 0
            
            while self.crawl_queue and crawled_count < max_nodes:
                # Pop the highest priority node (closest to Parque Hidalgo)
                curr = self.crawl_queue.pop(0)
                pano_id = curr["pano_id"]
                
                if pano_id in self.visited_panos:
                    # Load metadata directly from local cache to represent incremental memory
                    meta_path = os.path.join(self.cache_dir, pano_id, "metadata.json")
                    if os.path.exists(meta_path):
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        crawled_nodes.append(meta)
                        crawled_count += 1
                    continue
                    
                node_dir = os.path.join(self.cache_dir, pano_id)
                metadata_path = os.path.join(node_dir, "metadata.json")
                panorama_path = os.path.join(node_dir, "panorama.png")
                
                # Fetch public metadata
                meta = self.fetch_public_metadata(pano_id=pano_id)
                if not meta:
                    self.failed_panos[pano_id] = {
                        "retries": self.failed_panos.get(pano_id, {}).get("retries", 0) + 1,
                        "reason": "network_timeout"
                    }
                    self.save_state()
                    continue
                    
                # 3. Enforce Oldest Timeline Variant Selection
                timeline = meta.get("timeline", [])
                oldest_pano_id = pano_id
                oldest_date = meta.get("date", "9999-12") # default to far future if blank
                
                # Compare dates chronologically to extract the oldest capture variant
                for tl in timeline:
                    tl_id = tl["pano_id"]
                    tl_date = tl["date"]
                    if tl_date and tl_date < oldest_date:
                        oldest_pano_id = tl_id
                        oldest_date = tl_date
                        
                download_target_id = pano_id
                if oldest_pano_id != pano_id:
                    print(f"[Temporal Chronology] Found older timeline state: {oldest_pano_id} ({oldest_date}) replaces modern {pano_id}.")
                    oldest_meta = self.fetch_public_metadata(pano_id=oldest_pano_id)
                    if oldest_meta:
                        meta = oldest_meta
                        pano_id = oldest_pano_id
                        download_target_id = oldest_pano_id
                    else:
                        print(f"[Temporal Chronology] Historical meta returned null (archived legacy node). Keeping modern spatial metadata but targeting historical tiles for download: {oldest_pano_id}")
                        meta["date"] = oldest_date
                        meta["historical_pano_id"] = oldest_pano_id
                        download_target_id = oldest_pano_id
                        
                # 4. Download and stitch authentic tiles (prohibiting synthetic fallbacks)
                print(f"[Crawler] Crawling Node: {pano_id} (Tile Target: {download_target_id})")
                pano_img = self.download_and_stitch_tiles(download_target_id, zoom=3, allow_synthetic=False)
                
                if pano_img:
                    os.makedirs(node_dir, exist_ok=True)
                    pano_img.save(panorama_path)
                    
                    # Store raw metadata before preprocessing
                    with open(metadata_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=4)
                        
                    self.visited_panos.add(pano_id)
                    meta["image_path"] = os.path.abspath(panorama_path)
                    crawled_nodes.append(meta)
                    crawled_count += 1
                    
                    # 5. Enqueue connected spatial links (graph edges) within Bounding Box limits
                    for link in meta.get("adjacent_links", []):
                        link_id = link["pano_id"]
                        
                        # Fetch coordinate of adjacent link to inspect bounding box and sort priority
                        link_meta = self.fetch_public_metadata(pano_id=link_id)
                        if link_meta:
                            l_lat = link_meta["latitude"]
                            l_lon = link_meta["longitude"]
                            
                            if self.is_within_bbox(l_lat, l_lon):
                                self.queue_node(link_id, l_lat, l_lon)
                                
                                # Record graph connectivity edge
                                self.road_graph.append({
                                    "u": pano_id,
                                    "v": link_id,
                                    "yaw": link["yaw_deg"]
                                })
                                
                    # Save incremental scraper memory
                    self.save_state()
                else:
                    self.failed_panos[pano_id] = {
                        "retries": self.failed_panos.get(pano_id, {}).get("retries", 0) + 1,
                        "reason": "stitch_failure"
                    }
                    self.save_state()
                    
                time.sleep(0.4)  # Throttling
                
            print(f"[Crawler] Progressive crawl finished. Visited total: {len(self.visited_panos)} nodes.")
            return crawled_nodes
        finally:
            self.close()
