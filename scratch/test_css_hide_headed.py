import sys
import time
import os
from playwright.sync_api import sync_playwright

def test_hide_headed():
    url = "https://www.google.com/maps/@32.573484,-116.627276,3a,60y,0h,90t/data=!3m6!1e1!3m4!1s-u7R-O7Z7Xy6q8w14x8jSw!2e0"
    print(f"Navigating to {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until="load", timeout=30000)
        page.wait_for_selector("canvas", timeout=15000)
        
        # Wait 3.5 seconds
        time.sleep(3.5)
        
        # Inject CSS to hide all Google Maps overlays completely
        page.evaluate("""
            () => {
                const style = document.createElement('style');
                style.id = 'clean-streetview-style';
                style.textContent = `
                    .Owrmqf, .pzfvzf, .XltNde, .w6VYqd, .l4mL3, .TorxFf, .PlF8V, .F63Kk, .bqcX3e, .EtdG7d, .e9Chtd,
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
        
        # Take a screenshot to verify
        os.makedirs("data/screenshots", exist_ok=True)
        page.screenshot(path="data/screenshots/after_hide_headed.png")
        print("Captured after_hide_headed.png")
        
        browser.close()

if __name__ == "__main__":
    test_hide_headed()
