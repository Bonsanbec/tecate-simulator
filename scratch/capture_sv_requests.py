import sys
import time
import os
import re
import urllib.parse
from playwright.sync_api import sync_playwright

def inspect():
    lat = 32.573229
    lon = -116.626536
    url = f"https://www.google.com/maps/@{lat},{lon},18z"
    print(f"Navigating to {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--ignore-gpu-blocklist",
                "--disable-web-security"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Intercept and log all request/response details
        network_logs = []
        def intercept_response(response):
            r_url = response.url
            try:
                # Capture all requests with "pb=" or "photo" or "rpc"
                if "pb=" in r_url or "photo" in r_url or "rpc" in r_url or "cbk" in r_url:
                    text = response.text()
                    network_logs.append({
                        "url": r_url,
                        "status": response.status,
                        "response_text": text
                    })
            except Exception as e:
                pass

        page.on("response", intercept_response)
        
        page.goto(url, wait_until="load", timeout=30000)
        time.sleep(5)
        
        # Click Pegman button
        pegman = page.locator(".sHj5c.a8QCmb").first
        if pegman.is_visible():
            pegman.click()
            time.sleep(2)
            
            # Click left road offset (-150, 0)
            center_x = 640
            center_y = 360
            page.mouse.click(center_x - 150, center_y)
            time.sleep(8)
            
            print("\nCaptured Network Logs containing pb/photo/rpc/cbk:")
            for log in network_logs:
                print("-" * 80)
                print(f"URL: {log['url'][:200]}")
                print(f"Status: {log['status']}")
                print(f"Response (first 300 chars): {log['response_text'][:300]}")
            
        browser.close()

if __name__ == "__main__":
    inspect()
