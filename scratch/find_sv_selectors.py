import sys
import time
import os
from playwright.sync_api import sync_playwright

def find_selectors():
    lat = 32.573229
    lon = -116.626536
    # Let's use 90t (horizontal) and a real pano
    url = "https://www.google.com/maps/@32.573484,-116.627276,3a,60y,0h,90t/data=!3m6!1e1!3m4!1s-u7R-O7Z7Xy6q8w14x8jSw!2e0"
    print(f"Navigating to {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until="load", timeout=30000)
        time.sleep(5)
        
        # Capture screenshot before hiding
        os.makedirs("data/screenshots", exist_ok=True)
        page.screenshot(path="data/screenshots/before_hide.png")
        print("Captured before_hide.png")
        
        # Let's query elements with coordinates and size that overlay the canvas
        # and list their ids, classes, tags
        overlays = page.evaluate("""() => {
            const results = [];
            const walk = (node) => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    // Check if it's visible, absolute/fixed positioned, and not a parent of the canvas or canvas itself
                    const isCanvas = node.tagName.toLowerCase() === 'canvas';
                    const hasPosition = ['absolute', 'fixed'].includes(style.position);
                    const isVisible = rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                    
                    if (hasPosition && isVisible && !isCanvas && rect.width < 1280) {
                        results.push({
                            tag: node.tagName.toLowerCase(),
                            id: node.id,
                            className: node.className,
                            rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
                            ariaLabel: node.getAttribute('aria-label')
                        });
                    }
                }
                for (let child of node.childNodes) {
                    walk(child);
                }
            };
            walk(document.body);
            return results;
        }""")
        
        print(f"Found {len(overlays)} absolute/fixed overlay elements:")
        for idx, item in enumerate(overlays):
            print(f"[{idx}] tag={item['tag']}, id={item['id']!r}, class={item['className']!r}, rect={item['rect']}, label={item['ariaLabel']!r}")
            
        browser.close()

if __name__ == "__main__":
    find_selectors()
