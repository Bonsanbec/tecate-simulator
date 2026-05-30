import sys
import time
import os
from playwright.sync_api import sync_playwright

def test_pruner():
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
        
        # Wait 5 seconds for tiles to load and stabilize
        time.sleep(5)
        
        # Keep ONLY the canvas and its ancestors, delete EVERYTHING else!
        page.evaluate("""
            () => {
                console.log("Running ultimate canvas pruner...");
                const canvas = document.querySelector('canvas');
                if (!canvas) {
                    console.log("Canvas not found!");
                    return;
                }
                
                // Get all elements in document
                const all = Array.from(document.querySelectorAll('*'));
                let removedCount = 0;
                
                all.forEach(el => {
                    // If element is not canvas and does not contain canvas
                    if (el !== canvas && !el.contains(canvas)) {
                        // Check if it's still in the document before removing
                        if (el.parentNode) {
                            el.remove();
                            removedCount++;
                        }
                    }
                });
                
                console.log("Ultimate pruner finished. Removed " + removedCount + " elements.");
            }
        """)
        
        time.sleep(2)
        
        # Take a screenshot to verify
        os.makedirs("data/screenshots", exist_ok=True)
        screenshot_path = "data/screenshots/test_ultimate_pruner.png"
        page.screenshot(path=screenshot_path)
        print(f"Captured {screenshot_path}")
        
        browser.close()

if __name__ == "__main__":
    test_pruner()
