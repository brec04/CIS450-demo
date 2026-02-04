import os
from PIL import Image

photos_dir = "../photos"
output_dir = "."

TARGET_WIDTH = 640

for filename in os.listdir(photos_dir):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        img_path = os.path.join(photos_dir, filename)

        with Image.open(img_path) as img:
            original_width, original_height = img.size

            scale_ratio = TARGET_WIDTH / original_width
            new_height = round(original_height * scale_ratio)

            resized_img = img.resize((TARGET_WIDTH, new_height))

            name, _ = os.path.splitext(filename)
            output_filename = f"{name}-640x{new_height}.png"
            output_path = os.path.join(output_dir, output_filename)

            resized_img.save(output_path)

            print(f"Saved {output_filename}")
