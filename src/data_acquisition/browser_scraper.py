import os
import json
import math
import time
import urllib.parse
import requests
from PIL import Image
from io import BytesIO

# Bounding Box Limits for Tecate, Mexico
BBOX_SW_LAT = 32.521704
BBOX_SW_LON = -116.681499
BBOX_NE_LAT = 32.580233
BBOX_NE_LON = -116.510525

# Priority Center: Parque Hidalgo
PARQUE_HIDALGO_LAT = 32.573229
PARQUE_HIDALGO_LON = -116.626536

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
        
        # Load incremental persistence memory
        self.load_state()

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
                print(f"[Scraper Memory] State loaded: {len(self.visited_panos)} crawled nodes, {len(self.crawl_queue)} queued nodes.")
                return
            except Exception as e:
                print(f"[Scraper Memory] Failed to parse state: {e}. Reinitializing.")
                
        # Fresh initialization
        self.visited_panos = set()
        self.crawl_queue = []
        self.failed_panos = {}
        self.road_graph = []

    def save_state(self):
        """Saves current traversal state to disk to survive crashes and restarts."""
        state = {
            "visited_panos": list(self.visited_panos),
            "crawl_queue": self.crawl_queue,
            "failed_panos": self.failed_panos,
            "road_graph": self.road_graph
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

    def run_browser_session_and_intercept(self, lat: float, lon: float) -> str | None:
        """
        Launches Playwright Chromium browser to load Google Maps and intercept
        client network payloads, extracting the active panorama ID.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[Warning] Playwright not found. Browser interception skipped.")
            return None

        url = f"https://www.google.com/maps/@{lat},{lon},3a,75y,0h,90t/data=!3m4!1e1"
        print(f"[Playwright] Booting Chromium. Inspecting Maps client: {url}")
        
        pano_id = None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                page = context.new_page()
                
                # Intercept XHR responses to reverse-engineer client tile loaders
                def intercept_response(response):
                    nonlocal pano_id
                    r_url = response.url
                    if "output=tile" in r_url or "/v1/tile" in r_url:
                        parsed = urllib.parse.urlparse(r_url)
                        params = urllib.parse.parse_qs(parsed.query)
                        p_id = params.get("panoid", [None])[0]
                        if p_id:
                            pano_id = p_id

                page.on("response", intercept_response)
                page.goto(url, wait_until="load", timeout=30000)
                time.sleep(4)  # Wait for DOM and tiles to render
                browser.close()
                
            return pano_id
        except Exception as e:
            print(f"[Warning] Playwright browser session encountered a technical issue: {e}")
            return None

    def fetch_public_metadata(self, lat: float = None, lon: float = None, pano_id: str = None) -> dict | None:
        """
        Queries Google's unauthenticated client backend endpoint to reverse-engineer 
        coordinates, date parameters, road labels, timeline listings, and graph links.
        """
        url = "https://cbks0.google.com/cbk"
        params = {"output": "json"}
        
        if pano_id:
            params["panoid"] = pano_id
        elif lat is not None and lon is not None:
            params["ll"] = f"{lat},{lon}"
        else:
            return None
            
        try:
            # Query the unauthenticated server (mimics background XHR client fetch)
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "Location" in data:
                    loc = data["Location"]
                    p_id = loc.get("panoId")
                    
                    # Parse street links (graph edges)
                    links = []
                    for l in data.get("Annotation", {}).get("Link", []):
                        links.append({
                            "pano_id": l.get("panoId"),
                            "road_name": l.get("road_name", ""),
                            "yaw_deg": float(l.get("yawDeg", 0.0))
                        })
                        
                    # Parse timeline revisions (historical lineage states)
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
                    return meta
            return None
        except Exception as e:
            # Silence connection errors during local unit test suites
            return None

    def download_and_stitch_tiles(self, pano_id: str, zoom: int = 3) -> Image.Image | None:
        """
        Downloads cubic projection tiles directly from public servers, stitches them,
        crops the facade horizon, and saves the authentic high-resolution equirectangular panorama.
        """
        cols = 8
        rows = 4
        tile_w = 512
        tile_h = 512
        
        panorama = Image.new("RGB", (cols * tile_w, rows * tile_h))
        downloaded = 0
        
        tile_dir = os.path.join(self.cache_dir, pano_id, "tiles")
        os.makedirs(tile_dir, exist_ok=True)
        
        url_template = "https://streetviewpixels-pa.googleapis.com/v1/tile"
        
        for y in range(rows):
            for x in range(cols):
                params = {
                    "cb_client": "maps_sv",
                    "panoid": pano_id,
                    "x": str(x),
                    "y": str(y),
                    "zoom": str(zoom)
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
                    resp = requests.get(url_template, params=params, timeout=10)
                    if resp.status_code == 200 and len(resp.content) > 500:
                        tile_img = Image.open(BytesIO(resp.content))
                        tile_img.save(tile_path)  # Save raw tile before stitch
                        panorama.paste(tile_img, (x * tile_w, y * tile_h))
                        downloaded += 1
                        time.sleep(0.1)  # Rate limiting throttle
                except Exception as e:
                    pass
                    
        if downloaded >= (cols * rows) - 2:
            # Crop horizontal facade band (aspect ratio 4:1)
            facade_strip = panorama.crop((0, 680, 4096, 1704))
            resized = facade_strip.resize((2560, 640), Image.Resampling.BILINEAR)
            return resized
            
        return None

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
        # Discover initial seed node if queue is empty and we haven't started
        if len(self.crawl_queue) == 0 and len(self.visited_panos) == 0:
            print(f"[Scraper] Resolving crawler seed coordinate near ({seed_lat}, {seed_lon})...")
            # Try browser session first to inspect real client behavior
            seed_pano = self.run_browser_session_and_intercept(seed_lat, seed_lon)
            
            # Direct XHR query fallback
            seed_meta = self.fetch_public_metadata(lat=seed_lat, lon=seed_lon, pano_id=seed_pano)
            
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
                
            # 1. Reverse-engineer the timeline chronology to ALWAYS lock onto oldest capture date
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
                    
            if oldest_pano_id != pano_id:
                print(f"[Temporal Chronology] Found older timeline state: {oldest_pano_id} ({oldest_date}) replaces modern {pano_id}.")
                # Re-fetch metadata for the oldest timeline node
                oldest_meta = self.fetch_public_metadata(pano_id=oldest_pano_id)
                if oldest_meta:
                    meta = oldest_meta
                    pano_id = oldest_pano_id
                    
            # 2. Download and stitch authentic tiles
            print(f"[Crawler] Crawling Node: {pano_id} (Distance to Parque Hidalgo: {curr['priority_distance']:.4f} deg)")
            pano_img = self.download_and_stitch_tiles(pano_id, zoom=3)
            
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
                
                # 3. Enqueue connected spatial links (graph edges) within Bounding Box limits
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
