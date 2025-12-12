import cv2
import os
import time
import sys

def main():
    # Directory containing images
    image_folder = 'images'
    
    # Check if folder exists
    if not os.path.exists(image_folder):
        print(f"Error: Folder '{image_folder}' not found.")
        return

    # Get list of valid image files
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(valid_extensions)]
    images.sort() # Sort alphabetically

    if not images:
        print(f"No images found in '{image_folder}'.")
        return

    print(f"Found {len(images)} images. Starting slideshow...")
    print("Press 'q' to quit.")

    # Create a named window and set to full screen
    window_name = 'Slideshow'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        while True:
            for image_file in images:
                image_path = os.path.join(image_folder, image_file)
                img = cv2.imread(image_path)

                if img is None:
                    print(f"Failed to load image: {image_path}")
                    continue

                cv2.imshow(window_name, img)

                # Wait for 3000 ms (3 seconds)
                # cv2.waitKey returns the ASCII value of the key pressed
                key = cv2.waitKey(3000)

                # If 'q' is pressed, exit
                if key == ord('q'):
                    print("Quitting slideshow.")
                    return

    except KeyboardInterrupt:
        print("\nSlideshow interrupted.")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
