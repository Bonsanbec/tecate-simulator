import sys
import time
import os
from playwright.sync_api import sync_playwright

def test_shadow():
    lat = 32.573484
    lon = -116.627276
    pano_id = "-u7R-O7Z7Xy6q8w14x8jSw"
    heading = 180.0
    
    url = f"https://www.google.com/maps?layer=c&cbll={lat},{lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0"
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
        
        time.sleep(5)
        
        # Inject JavaScript to hide ALL overlays including shadow DOM elements recursively
        page.evaluate("""
            () => {
                function hideInShadow(root) {
                    if (!root) return;
                    
                    const selectors = [
                        '.Owrmqf', '.C5SiJf', '.fBpDtb', '.b3vVFf', '.TorxFf', '.PlF8V', '.F63Kk', '.bqcX3e', '.EtdG7d', '.e9Chtd',
                        '.noprint', '.gmnoprint', '.gm-style-cc',
                        '[class*="place-card"]', '#titlecard',
                        '#minimap', '[class*="minimap"]',
                        '#layers-menu', '#compass', '#widget-zoom',
                        '#watermark', '[class*="watermark"]',
                        'button[aria-label*="Back"]', '.gm-control-active',
                        '[aria-label*="Back to map"]'
                    ];
                    
                    selectors.forEach(sel => {
                        try {
                            const elms = root.querySelectorAll(sel);
                            elms.forEach(el => {
                                el.style.setProperty('display', 'none', 'important');
                            });
                        } catch (e) {}
                    });
                    
                    // Also traverse any child elements
                    const all = root.querySelectorAll('*');
                    all.forEach(el => {
                        if (el.shadowRoot) {
                            hideInShadow(el.shadowRoot);
                        }
                    });
                }
                
                // Run on document and all shadow roots
                hideInShadow(document);
            }
        """)
        
        # Take a screenshot to verify
        os.makedirs("data/screenshots", exist_ok=True)
        page.screenshot(path="data/screenshots/test_shadow_dom.png")
        print("Captured test_shadow_dom.png")
        
        browser.close()

if __name__ == "__main__":
    test_shadow()
