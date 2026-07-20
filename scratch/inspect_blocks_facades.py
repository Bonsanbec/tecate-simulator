import json
import os

print("--- Checking blocks_cache.json ---")
with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

print("Total blocks (manzanas):", len(blocks))
sample_block_id = list(blocks.keys())[0]
print("Sample Block ID:", sample_block_id)
print("Sample Block content:", json.dumps(blocks[sample_block_id], indent=2)[:500])

print("\n--- Checking facades_cache.json ---")
with open("data/facades_cache.json", "r") as f:
    facades = json.load(f)

print("Total facades:", len(facades))
sample_facade_id = list(facades.keys())[0]
print("Sample Facade ID:", sample_facade_id)
print("Sample Facade content keys:", list(facades[sample_facade_id].keys()) if isinstance(facades[sample_facade_id], dict) else type(facades[sample_facade_id]))

