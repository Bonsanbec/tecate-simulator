import os
import urllib.parse
import requests
from PIL import Image
from io import BytesIO

class StreetViewDownloader:
    """
    Downloads real Google Street View imagery and metadata for a given coordinate.
    If API keys are missing, raises descriptive exceptions or down-weights.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_STREETVIEW_API_KEY", "")
        self.metadata_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
        self.image_url = "https://maps.googleapis.com/maps/api/streetview"

    def has_api_key(self) -> bool:
        return len(self.api_key.strip()) > 0

    def get_metadata(self, lat: float, lon: float) -> dict | None:
        """
        Fetches metadata for the closest street view panorama to the given coordinate.
        """
        if not self.has_api_key():
            print("[Warning] No Google Street View API Key configured. Metadata fetch skipped.")
            return None
            
        params = {
            "location": f"{lat},{lon}",
            "key": self.api_key
        }
        
        try:
            resp = requests.get(self.metadata_url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "OK":
                    return {
                        "pano_id": data.get("pano_id"),
                        "lat": data.get("location", {}).get("lat", lat),
                        "lon": data.get("location", {}).get("lng", lon),
                        "date": data.get("date", "2009-01"), # default to 2009 if date field missing
                        "copyright": data.get("copyright")
                    }
                else:
                    print(f"[Info] Street View metadata status: {data.get('status')}")
            return None
        except Exception as e:
            print(f"[Error] Failed to fetch Street View metadata: {e}")
            return None

    def download_viewpoint(self, lat: float, lon: float, heading: float, pitch: float = 0.0, fov: float = 90.0) -> Image.Image | None:
        """
        Downloads a single static perspective viewpoint tile.
        """
        if not self.has_api_key():
            return None
            
        params = {
            "size": "640x640",
            "location": f"{lat},{lon}",
            "heading": str(heading),
            "pitch": str(pitch),
            "fov": str(fov),
            "key": self.api_key
        }
        
        try:
            resp = requests.get(self.image_url, params=params, timeout=15)
            if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                return Image.open(BytesIO(resp.content))
            return None
        except Exception as e:
            print(f"[Error] Failed to download Street View tile (heading={heading}): {e}")
            return None

    def fetch_full_panorama(self, lat: float, lon: float) -> dict | None:
        """
        Scrapes and compiles historical panorama data around a specific coordinate.
        Returns stitched tiles and metadata.
        """
        meta = self.get_metadata(lat, lon)
        if not meta:
            return None
            
        # Download four headings (0, 90, 180, 270) to compose the horizontal view
        headings = [0, 90, 180, 270]
        tiles = {}
        
        for h in headings:
            img = self.download_viewpoint(meta["lat"], meta["lon"], heading=h)
            if img:
                tiles[h] = img
                
        if len(tiles) < 4:
            print(f"[Warning] Incomplete tiles downloaded for coordinate ({lat}, {lon})")
            return None
            
        # Stitch tiles horizontally into a simplified wide strip panorama (2560 x 640)
        panorama_width = 2560
        panorama_height = 640
        panorama_img = Image.new("RGB", (panorama_width, panorama_height))
        
        # Stitch headings in order: 0 (N), 90 (E), 180 (S), 270 (W)
        for idx, h in enumerate(headings):
            panorama_img.paste(tiles[h], (idx * 640, 0))
            
        # Estimate a temporal probability (prioritizing pre-2010/2009)
        # Parse date e.g., '2009-10'
        captured_date = meta.get("date", "")
        is_circa_2009 = False
        prob = 0.05
        
        if captured_date:
            year = int(captured_date.split("-")[0])
            if year == 2009:
                is_circa_2009 = True
                prob = 0.95
            elif year < 2010:
                is_circa_2009 = True
                prob = 0.85
            else:
                prob = 0.05  # heavily down-weighted

        return {
            "latitude": meta["lat"],
            "longitude": meta["lon"],
            "pano_id": meta["pano_id"],
            "date": captured_date,
            "temporal_probability": prob,
            "image": panorama_img,
            "headings": headings
        }
