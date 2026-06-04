import json

def extract_block():
    target_block_id = "block_lat_32.57255_lon_-116.62529"
    with open("export/reconstruction_export.json", "r") as f:
        # Since it is huge, let's read it block-by-block if possible, 
        # or load the whole thing if memory allows. Let's do it carefully.
        # Python json.load can load 600MB in a few seconds on a Mac.
        print("Loading reconstruction_export.json...")
        data = json.load(f)
        print("Loaded. Looking for block...")
        for block in data.get("blocks", []):
            if block["block_id"] == target_block_id:
                print("Found target block!")
                with open("scratch/target_block_details.json", "w") as out:
                    json.dump(block, out, indent=2)
                print("Saved target block details to scratch/target_block_details.json")
                return
        print("Block not found!")

if __name__ == "__main__":
    extract_block()
