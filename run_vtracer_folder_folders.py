import os
import subprocess

# Define input and output directories
parent_input_folder = "artworks_cvpr/wikiart_resized"
parent_output_folder = "input_svg/wikiart_resized/"

# Ensure the base output directory exists
os.makedirs(parent_output_folder, exist_ok=True)

# Iterate through each subfolder in the parent input folder
for subfolder in os.listdir(parent_input_folder):
    subfolder_path = os.path.join(parent_input_folder, subfolder)

    # Ensure it's a directory before processing
    if os.path.isdir(subfolder_path):
        output_subfolder = os.path.join(parent_output_folder, subfolder)
        os.makedirs(output_subfolder, exist_ok=True)  # Create output subfolder

        # Iterate through images in the current subfolder
        for file in os.listdir(subfolder_path):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                input_path = os.path.join(subfolder_path, file)
                output_filename = f"{file.rsplit('.', 1)[0]}.svg"
                output_path = os.path.join(output_subfolder, output_filename)

                cmd = [
                    "vtracer.exe",  # Ensure vtracer.exe is in the system PATH or provide full path
                    "--input",
                    input_path,
                    "--output",
                    output_path,
                    "--hierarchical",
                    "cutout",
                    "-f",
                    "0",
                    "-p",
                    "8",
                    "-g",
                    "12",
                    "-l",
                    "3.5",
                    "-s",
                    "0",
                ]

                try:
                    subprocess.run(cmd, check=True)
                    print(f"Converted: {input_path} -> {output_path}")
                except subprocess.CalledProcessError as e:
                    print(f"Error processing {input_path}: {e}")
