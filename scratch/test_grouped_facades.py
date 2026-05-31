def group_adjacent_segments(segments):
    n = len(segments)
    if n == 0:
        return []
        
    # Find a starting index that is a transition boundary to simplify circular grouping
    start_idx = 0
    for i in range(n):
        prev = segments[(i - 1) % n]
        curr = segments[i]
        if (curr["pano_id"] != prev["pano_id"] or 
            curr["pano_id"] is None or 
            abs(curr["heading"] - prev["heading"]) > 2.0):
            start_idx = i
            break
            
    # Group sequentially starting from start_idx
    groups = []
    curr_group = [segments[start_idx]]
    
    for i in range(1, n):
        idx = (start_idx + i) % n
        curr = segments[idx]
        prev = curr_group[-1]
        
        if (curr["pano_id"] == prev["pano_id"] and 
            curr["pano_id"] is not None and 
            abs(curr["heading"] - prev["heading"]) <= 2.0):
            curr_group.append(curr)
        else:
            groups.append(curr_group)
            curr_group = [curr]
            
    groups.append(curr_group)
    return groups

# Test data representing facade segments around a 4-sided block
test_segments = [
    {"index": 0, "pano_id": "pano_A", "heading": 90.0, "A": (0, 0), "B": (5, 0)},
    {"index": 1, "pano_id": "pano_A", "heading": 90.0, "A": (5, 0), "B": (10, 0)},
    {"index": 2, "pano_id": "pano_B", "heading": 180.0, "A": (10, 0), "B": (10, 10)},
    {"index": 3, "pano_id": "pano_C", "heading": 270.0, "A": (10, 10), "B": (5, 10)},
    {"index": 4, "pano_id": "pano_C", "heading": 270.0, "A": (5, 10), "B": (0, 10)},
    {"index": 5, "pano_id": "pano_A", "heading": 90.0, "A": (0, 10), "B": (0, 0)} # Wrap matching
]

groups = group_adjacent_segments(test_segments)
print(f"Total groups found: {len(groups)}")
for idx, g in enumerate(groups):
    indices = [s["index"] for s in g]
    pano = g[0]["pano_id"]
    heading = g[0]["heading"]
    start_A = g[0]["A"]
    end_B = g[-1]["B"]
    print(f"  Group {idx}: Facades={indices}, Pano={pano}, Heading={heading}, Start={start_A}, End={end_B}")
