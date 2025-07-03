# from PIL import Image
# import os

# # Define folder paths
# base_folder = r"C:\Users\2813813\Downloads\image_rendering_ver06_0606\static"
# imgs_folder = os.path.join(base_folder, "test")
# # sketches_folder = os.path.join(base_folder, "sketches")
# sketches_bw_folder = os.path.join(base_folder, "sketches_bw")

# # Ensure output directory exists
# os.makedirs(sketches_bw_folder, exist_ok=True)

# # Process each image in the imgs folder
# for file in os.listdir(imgs_folder): # Only process JPG files
#         file_name = os.path.splitext(file)[0]  # Get filename without extension
#         exts=['.jpg','.png','.jpeg']
#         # Paths for original image, sketch, and output BW sketch
#         for e in exts:
#             image1_path = os.path.join(imgs_folder, f"{file_name}{e}")
#             if os.path.exists(image1_path):
#                 break
#         # image2_path = os.path.join(sketches_folder, f"{file_name}.png")
#         image2_bw_path = os.path.join(sketches_bw_folder, f"{file_name}.png")

#         # # Check if sketch exists
#         # if not os.path.exists(image2_path):
#         #     print(f"Skipping {file_name}: Sketch not found in 'sketches' folder.")
#         #     continue

#         # Load the original image and sketch
#         image1 = Image.open(image1_path)
#         # image2 = Image.open(image2_path)

#         # Resize sketch to match the original image if dimensions differ
#         # if image1.size != image2.size:
#         #     image2 = image2.resize(image1.size)

#         # Convert to grayscale and apply binary threshold
#         threshold = 180  # Adjust threshold as needed
#         binary_image = image1.convert("L").point(lambda p: 255 if p > threshold else 0)

#         # Save the black-and-white sketch
#         binary_image.save(image2_bw_path)

#         print(f"Processed and saved: {image2_bw_path}")


def convert_single_image_to_bw(
    image_path, output_path, threshold=180, save_additional_path=None
):
    """
    Converts a single image to black-and-white and saves it.

    Parameters:
    - image_path (str): Path to the input image (.jpg, .png, .jpeg).
    - output_path (str): Path to save the black-and-white image.
    - threshold (int): Threshold for binarization (0-255). Default is 180.
    - save_additional_path (str): Optional second path to also save the result.
    """
    try:
        image = Image.open(image_path).convert("L")
        bw_image = image.point(lambda p: 255 if p > threshold else 0)

        # Ensure output folder exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        bw_image.save(output_path)
        print(f"Saved to: {output_path}")

        # Optionally save to another path
        if save_additional_path:
            os.makedirs(os.path.dirname(save_additional_path), exist_ok=True)
            bw_image.save(save_additional_path)
            print(f"Also saved to: {save_additional_path}")

    except Exception as e:
        print(f"Failed to process image '{image_path}': {e}")
