
import cv2
import os
import glob

def crop_to_16_9(image_path):
    """
    Reads an image, rotates it if portrait, crops to 16:9, and overwrites the file.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read {image_path}")
        return

    height, width = img.shape[:2]

    # Rotate if portrait
    if height > width:
        print(f"Rotating {os.path.basename(image_path)}...")
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        height, width = img.shape[:2] # Update dimensions after rotation

    # Calculate target dimensions for 16:9
    target_ratio = 16 / 9
    current_ratio = width / height

    if current_ratio > target_ratio:
        # Image is too wide, crop width
        new_width = int(height * target_ratio)
        offset = (width - new_width) // 2
        img = img[:, offset:offset+new_width]
    elif current_ratio < target_ratio:
        # Image is too tall, crop height
        new_height = int(width / target_ratio)
        offset = (height - new_height) // 2
        img = img[offset:offset+new_height, :]
    
    # Save overwritten
    cv2.imwrite(image_path, img)
    print(f"Processed: {os.path.basename(image_path)}")

def main():
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    
    # Supports common image formats
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    image_files = []
    
    for ext in extensions:
        # Case insensitive search might fail on unix with glob, relying on extensions list
        # We'll just search for exact matches as provided
        image_files.extend(glob.glob(os.path.join(images_dir, ext)))
        image_files.extend(glob.glob(os.path.join(images_dir, ext.upper())))

    print(f"Found {len(image_files)} images.")

    for img_path in image_files:
        try:
            crop_to_16_9(img_path)
        except Exception as e:
            print(f"Failed to process {img_path}: {e}")

if __name__ == "__main__":
    main()
