import sys
import time
import os
from playwright.sync_api import sync_playwright

def test_ultimate():
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
        
        page.on("console", lambda msg: print(f"[Browser Console] {msg.text}"))
        
        page.goto(url, wait_until="load", timeout=30000)
        page.wait_for_selector("canvas", timeout=15000)
        
        time.sleep(5)
        
        # Keep ONLY the canvas/scene container and delete EVERYTHING else!
        page.evaluate("""
            () => {
                console.log("Running ultimate clean...");
                
                // Find the Street View main container (.gm-style or similar)
                const canvas = document.querySelector('canvas');
                if (!canvas) {
                    console.log("Canvas not found!");
                    return;
                }
                
                // Find the top-most wrapper of the Street View viewport
                let svContainer = canvas;
                while (svContainer && svContainer.parentElement && svContainer.parentElement !== document.body) {
                    if (svContainer.className.includes('gm-style') || svContainer.className.includes('widget-scene')) {
                        break;
                    }
                    svContainer = svContainer.parentElement;
                }
                
                if (!svContainer) {
                    console.log("Street View container not found!");
                    return;
                }
                
                console.log("Found Street View container tag:", svContainer.tagName, "class:", svContainer.className);
                
                // Let's hide all sibling elements of the Street View container
                let parent = svContainer.parentElement;
                while (parent) {
                    Array.from(parent.children).forEach(child => {
                        if (child !== svContainer && !child.contains(svContainer)) {
                            console.log("Removing sibling:", child.tagName, "class:", child.className);
                            child.remove();
                        }
                    });
                    svContainer = parent;
                    parent = parent.parentElement;
                }
                
                // Let's also search inside the remaining scene wrapper for any absolute overlay divs (excluding canvas)
                const overlays = document.querySelectorAll('.gm-style > div:not(:first-child)');
                overlays.forEach(el => {
                    console.log("Removing child overlay:", el.tagName, "class:", el.className);
                    el.remove();
                });
            }
        """)
        
        time.sleep(2)
        
        # Take a screenshot to verify
        os.makedirs("data/screenshots", exist_ok=True)
        page.screenshot(path="data/screenshots/test_ultimate_clean.png")
        print("Captured test_ultimate_clean.png")
        
        browser.close()

if __name__ == "__main__":
    test_ultimate()
