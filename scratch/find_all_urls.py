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
        
        all_urls = []
        def intercept_response(response):
            r_url = response.url
            all_urls.append(r_url)

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
            
            print("\nList of all unique URLs requested during Street View activation:")
            # Filter and sort unique URLs to keep it readable
            unique_domains_and_endpoints = set()
            for u in all_urls:
                parsed = urllib.parse.urlparse(u)
                path = parsed.path
                domain = parsed.netloc
                # Group by domain + path
                unique_domains_and_endpoints.add(f"{domain}{path}")
                
            for u in sorted(list(unique_domains_and_endpoints)):
                print(u)
            
        browser.close()

if __name__ == "__main__":
    inspect()
