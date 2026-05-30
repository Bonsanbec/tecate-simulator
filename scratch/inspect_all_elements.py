import sys
import time
import os
from playwright.sync_api import sync_playwright

def inspect():
    url = "https://www.google.com/maps?layer=c&cbll=32.573484,-116.627276&panoid=-u7R-O7Z7Xy6q8w14x8jSw&cbp=11,180.00,,0,0"
    print(f"Navigating to {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until="load", timeout=30000)
        page.wait_for_selector("canvas", timeout=15000)
        time.sleep(5)
        
        # Query ALL visible elements that have some text or might be UI overlays
        elements = page.evaluate("""() => {
            const results = [];
            const all = document.querySelectorAll('*');
            all.forEach(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                if (rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden') {
                    // Check if it has class or ID
                    if (el.id || el.className) {
                        results.push({
                            tag: el.tagName.toLowerCase(),
                            id: el.id,
                            className: el.className,
                            text: el.innerText ? el.innerText.substring(0, 30) : '',
                            rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
                            zIndex: style.zIndex,
                            position: style.position
                        });
                    }
                }
            });
            return results;
        }""")
        
        print(f"Found {len(elements)} visible elements with class/ID:")
        for idx, item in enumerate(elements):
            if any(term in str(item).lower() for term in ['tijuana', 'compartir', 'maps', 'streetview']):
                print(f"[{idx}] tag={item['tag']}, id={item['id']!r}, class={item['className']!r}, text={item['text']!r}, rect={item['rect']}, zIndex={item['zIndex']}, pos={item['position']}")
                
        browser.close()

if __name__ == "__main__":
    inspect()
