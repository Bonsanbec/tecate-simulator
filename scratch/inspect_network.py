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
    
    intercepted_urls = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        def intercept_response(response):
            r_url = response.url
            if "panoid=" in r_url or "photo" in r_url:
                intercepted_urls.append(r_url)

        page.on("response", intercept_response)
        
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
            print("Clicked map offset.")
            time.sleep(8)
            
        print("\n=== FINAL STATE ===")
        print(f"page.url: {page.url}")
        print(f"window.location.href: {page.evaluate('window.location.href')}")
        
        print("\n=== INTERCEPTED PANOS/PHOTOS REQUESTS ===")
        for i_url in intercepted_urls:
            if "panoid=" in i_url or "photo" in i_url:
                print(f" - {i_url[:160]}")
                
        browser.close()

if __name__ == "__main__":
    inspect()
