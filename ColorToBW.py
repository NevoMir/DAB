import cv2
import os
import shutil
import time

def convert_to_bw():
    # Define paths (Root of Repo)
    # The script assumes it runs from the repo root or these folders are in the CWD.
    input_dir = "Color"
    output_dir = "BlackAndWhite"

    # 1. Verify Input
    if not os.path.exists(input_dir):
        print(f"Error: Input folder '{input_dir}' does not exist.")
        return

    # 2. Setup Output Folder (Overwrite/Clear)
    if os.path.exists(output_dir):
        print(f"Clearing existing output folder '{output_dir}'...")
        shutil.rmtree(output_dir)
    
    os.makedirs(output_dir)
    print(f"Created output folder '{output_dir}'.")

    # 3. Process Images
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
    
    if not files:
        print("No images found in Color folder.")
        return

    print(f"Processing {len(files)} images...")
    
    for filename in sorted(files):
        # Read
        input_path = os.path.join(input_dir, filename)
        img = cv2.imread(input_path)
        
        if img is None:
            print(f"  Skipping {filename} (Load Failed)")
            continue
            
        # Convert to Grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Save
        output_path = os.path.join(output_dir, filename)
        try:
            cv2.imwrite(output_path, gray_img)
            print(f"  Converted: {filename}")
        except Exception as e:
            print(f"  Failed to save {filename}: {e}")

    print("\nConversion Complete.")
    print(f"Black and White images are in: {output_dir}")

if __name__ == "__main__":
    convert_to_bw()
