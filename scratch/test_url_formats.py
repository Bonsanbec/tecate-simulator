import sys
import time
import os
from playwright.sync_api import sync_playwright

def test_urls():
    lat = 32.573484
    lon = -116.627276
    pano_id = "-u7R-O7Z7Xy6q8w14x8jSw"
    
    # Let's test 3 different formats:
    formats = [
        # Format 0: Direct embed/viewer URL
        f"https://www.google.com/maps/@{lat},{lon},3a,60y,0h,90t/data=!3m6!1e1!3m4!1s{pano_id}!2e0",
        # Format 1: Query parameter format (classic link)
        f"https://maps.google.com/?cbll={lat},{lon}&layer=c&cbp=12,0,,0,0",
        # Format 2: Embed map player URL (very clean and lightweight!)
        f"https://www.google.com/maps/embed/v1/streetview?key=mock_key&location={lat},{lon}&heading=0&pitch=0&fov=60",
        # Format 3: Direct Street View standalone player URL
        f"https://www.google.com/maps?layer=c&cbll={lat},{lon}&panoid={pano_id}&cbp=11,0,,0,90"
    ]
    
    os.makedirs("data/screenshots/url_tests", exist_ok=True)
    
    with sync_playwright() as p:
        for idx, url in enumerate(formats):
            print(f"\nTesting Format {idx}: {url}")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="load", timeout=20000)
                time.sleep(6) # Let WebGL load
                
                screenshot_path = f"data/screenshots/url_tests/format_{idx}.png"
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}")
            except Exception as e:
                print(f"Error loading Format {idx}: {e}")
            finally:
                browser.close()

if __name__ == "__main__":
    test_urls()
