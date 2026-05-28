# Legal & Technical Limitations of Public Street View Web Scraping

This document outlines the architectural boundaries, reverse-engineering principles, legal terms, and operational guidelines for the browser-driven public Google Maps / Street View scraping subsystem.

---

## 1. Legal Boundaries & Terms of Service (ToS)

Scraping data directly from the public Google Maps client operates outside official API support and is subject to the following legal and technical considerations:

### Google Maps Terms of Service (Section 3.2.2)
- **Prohibition on Scraping**: Google's Terms of Service explicitly prohibit downloading, exporting, storing, or caching Map Content (including panoramas, tiles, coordinates, and road segments) without prior written authorization.
- **Reverse-Engineering Constraints**: Direct inspection or reverse-engineering of the JavaScript obfuscated code bundles (`maps/api/js` or client bundles) violates the licensing terms.
- **Fair Use & Academic Policy**: The software is designed as a *simulation, proxy research, and educational platform* for historical spatial reconstruction in academic settings. Commercial deployments using scraped assets face substantial legal risks of trademark infringement and service-access termination.

---

## 2. Technical Hurdles & Failure Modes

Because the scraper targets the public, live web client, it must assume a highly unstable environment:

| Failure Mode | Technical Cause | Pipeline Mitigation |
| :--- | :--- | :--- |
| **CAPTCHA / Bot Detection** | Rapid automated jumps or headless Chromium signatures. | The browser scraper emulates human browsing by persisting user profiles, rotating user-agents, introducing randomized cursor trajectories (`page.mouse.move`), and enforcing a 0.5s network throttle. |
| **IP Address Throttling** | High frequency tile requests (`zoom=3` requires 32 tiles per panorama). | The scraper enforces strict **local caching**. Once a panorama's tiles are stitched into `data/raw_scraped/{pano_id}/panorama.png`, the system never requests that node again. |
| **Undocumented JSON Payload Shifts** | Google modifying the internal `photometa` or `cbk` output structure. | The traversal engine uses robust fallback dictionary `.get()` calls and maps missing nodes directly to the GIS-graph prior. If a parsing error occurs, a procedural stucco facade material is automatically applied. |
| **Nonuniform Historical Coverage** | 2009 Street View data only covers a subset of primary avenues. | The pipeline extracts adjacent timeline frames from the unauthenticated public network packets, prioritizing the earliest available states while dynamically downweightting modern links. |

---

## 3. Request Tracing & Reverse Engineering Specifications

To stitch cubic/spherical panorama tiles, the scraper intercepts the unauthenticated backend tile server network traffic:

```
https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv&panoid={pano_id}&x={x}&y={y}&zoom={zoom}
```

### Tile Coordinate Mapping (`zoom=3` Layout):
For standard zoom level 3, the equirectangular sphere is projected onto an $8 \times 4$ grid of $512 \times 512$ pixel tiles:

```
 y-row
   0   [  0, 0 ] [  1, 0 ] [  2, 0 ] [  3, 0 ] [  4, 0 ] [  5, 0 ] [  6, 0 ] [  7, 0 ]
   1   [  0, 1 ] [  1, 1 ] [  2, 1 ] [  3, 1 ] [  4, 1 ] [  5, 1 ] [  6, 1 ] [  7, 1 ]
   2   [  0, 2 ] [  1, 2 ] [  2, 2 ] [  3, 2 ] [  4, 2 ] [  5, 2 ] [  6, 2 ] [  7, 2 ]
   3   [  0, 3 ] [  1, 3 ] [  2, 3 ] [  3, 3 ] [  4, 3 ] [  5, 3 ] [  6, 3 ] [  7, 3 ]
         x=0       x=1       x=2       x=3       x=4       x=5       x=6       x=7  (x-column)
```

The tile stitcher fetches these 32 tiles horizontally, projects them into a $4096 \times 2048$ spherical grid, crops the vertical horizon strip (pixel coordinate y-rows 680 to 1704), and resizes it to the standard $2560 \times 640$ horizontal equirectangular panorama.

---

## 4. Troubleshooting & DOM Modification Adaptability

If Google modifies their frontend classes or changes the DOM structure, follow this debugging runbook:

1. **Enable Headed Mode**:
   Modify `browser_scraper.py` parameter `headless = False` and execute:
   ```bash
   PYTHONPATH=. ./venv/bin/python -c "from src.data_acquisition.browser_scraper import GoogleStreetViewScraper; GoogleStreetViewScraper(headless=False).traverse_street_graph(32.5678, -116.6261, max_nodes=1)"
   ```
2. **Inspect Interception Logs**:
   Open Chromium's Developer Console (F12) to trace network requests.
   - If the tile URL base changes (e.g. from `/v1/tile` to `/v2/tile`), locate the new pattern in `browser_scraper.py` on line 185 and update the string matching filter.
   - If Google obfuscates the photometa response further, the scraper automatically falls back to querying the public unauthenticated `https://cbk0.google.com/cbk?output=json` endpoint directly using Python requests, which remains highly stable due to legacy mobile/client backwards-compatibility.
