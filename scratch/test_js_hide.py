import sys
import time
import os
from playwright.sync_api import sync_playwright

def test_js_hide():
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
        
        # Inject JavaScript to programmatically hide all overlays
        page.evaluate("""
            () => {
                const classesToHide = [
                    'Owrmqf', 'pzfvzf', 'XltNde', 'w6VYqd', 'l4mL3', 'TorxFf', 
                    'PlF8V', 'F63Kk', 'bqcX3e', 'EtdG7d', 'e9Chtd', 'noprint', 
                    'gmnoprint', 'gm-style-cc', 'place-card', 'titlecard', 
                    'minimap', 'compass', 'widget-zoom', 'watermark'
                ];
                
                classesToHide.forEach(cls => {
                    const elms = document.querySelectorAll(`[class*="${cls}"]`);
                    elms.forEach(el => {
                        el.style.setProperty('display', 'none', 'important');
                    });
                });
                
                const idsToHide = ['minimap', 'titlecard', 'compass', 'widget-zoom', 'watermark', 'searchboxcontainer'];
                idsToHide.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.style.setProperty('display', 'none', 'important');
                    }
                });
                
                // Hide absolute elements that are overlays
                const allElements = document.querySelectorAll('div, button, label, img');
                allElements.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    if (['absolute', 'fixed'].includes(style.position)) {
                        const isMainCanvas = el.tagName.toLowerCase() === 'canvas';
                        const isParentOfCanvas = el.contains(document.querySelector('canvas'));
                        if (!isMainCanvas && !isParentOfCanvas) {
                            el.style.setProperty('display', 'none', 'important');
                        }
                    }
                });
            }
        """)
        
        # Take a screenshot to verify
        os.makedirs("data/screenshots", exist_ok=True)
        page.screenshot(path="data/screenshots/test_js_hide.png")
        print("Captured test_js_hide.png")
        
        browser.close()

if __name__ == "__main__":
    test_js_hide()
