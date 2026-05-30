import sys
import time
import os
from playwright.sync_api import sync_playwright

def test_remove():
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
        
        # Programmatically remove all overlay elements from the DOM entirely!
        page.evaluate("""
            () => {
                const classesToRemove = [
                    'Owrmqf', 'C5SiJf', 'fBpDtb', 'b3vVFf', 'TorxFf', 'PlF8V', 
                    'F63Kk', 'bqcX3e', 'EtdG7d', 'e9Chtd', 'noprint', 
                    'gmnoprint', 'gm-style-cc', 'place-card', 'titlecard', 
                    'minimap', 'compass', 'widget-zoom', 'watermark'
                ];
                
                classesToRemove.forEach(cls => {
                    const elms = document.querySelectorAll(`[class*="${cls}"]`);
                    elms.forEach(el => {
                        console.log('Removing element:', el);
                        el.remove();
                    });
                });
                
                // Hide or remove absolute overlay divs
                const all = document.querySelectorAll('div, button, label, img');
                all.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (['absolute', 'fixed'].includes(style.position)) {
                        const isMainCanvas = el.tagName.toLowerCase() === 'canvas';
                        const isParentOfCanvas = el.contains(document.querySelector('canvas'));
                        if (!isMainCanvas && !isParentOfCanvas) {
                            el.remove();
                        }
                    }
                });
            }
        """)
        
        # Wait 1.0 second for layout reflow
        time.sleep(1.0)
        
        # Take a screenshot to verify
        os.makedirs("data/screenshots", exist_ok=True)
        page.screenshot(path="data/screenshots/test_remove.png")
        print("Captured test_remove.png")
        
        browser.close()

if __name__ == "__main__":
    test_remove()
