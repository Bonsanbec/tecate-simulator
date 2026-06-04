from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

def main():
    print("Loading model config...")
    model_name = "nvidia/segformer-b0-finetuned-ade-512-512"
    model = SegformerForSemanticSegmentation.from_pretrained(model_name)
    id2label = model.config.id2label
    
    # We want to find wall, window, door, sky
    target_labels = ["wall", "window", "door", "sky", "building"]
    
    print("\n=== Model Label Mapping ===")
    for idx, label in sorted(id2label.items(), key=lambda x: int(x[0])):
        label_lower = label.lower()
        if any(t in label_lower for t in target_labels):
            print(f"Index {idx}: {label}")

if __name__ == "__main__":
    main()
