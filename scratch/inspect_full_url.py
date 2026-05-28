import sys
import time
import os
from playwright.sync_api import sync_playwright

def inspect():
    lat = 32.573229
    lon = -116.626536
    url = f"https://www.google.com/maps/@{lat},{lon},18z"
    print(f"Navigating to {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        captured_requests = []
        
        def intercept_request(request):
            r_url = request.url
            if "photometa/v1" in r_url:
                captured_requests.append({
                    "url": r_url,
                    "headers": request.headers
                })

        page.on("request", intercept_request)
        
        page.goto(url, wait_until="load", timeout=30000)
        time.sleep(5)
        
        # Click Pegman button
        pegman = page.locator(".sHj5c.a8QCmb").first
        if pegman.is_visible():
            pegman.click()
            print("Clicked Pegman button.")
            time.sleep(2)
            
            # Click left road offset (-150, 0)
            center_x = 640
            center_y = 360
            page.mouse.click(center_x - 150, center_y)
            print("Clicked map offset to trigger Street View...")
            time.sleep(10)
            
        print("\n=== CAPTURED PHOTOMETA REQUESTS ===")
        for req in captured_requests:
            print(f"\nURL: {req['url']}")
            print("Headers:")
            print(json.dumps(req['headers'], indent=2))
            
        browser.close()

if __name__ == "__main__":
    import json
    inspect()
