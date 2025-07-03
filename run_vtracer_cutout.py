import os
import subprocess
import sys

input_folder = r"C:\Users\2813813\Downloads\image_rendering_ver04\static\thumbnails"  # f"{folder_name}/{filename}"#f"sam_outputs/{filename}"
output_folder = r"C:\Users\2813813\Downloads\image_rendering_ver04\static\svg_outputa"  # f"input_svg/{folder_name}/{filename}"
os.makedirs(output_folder, exist_ok=True)  # Ensure output directory exists

for file in os.listdir(input_folder):
    if file.lower().endswith((".png", ".jpg", ".jpeg")):
        input_path = os.path.join(input_folder, file)
        output_path = os.path.join(
            output_folder, "vtrace-" + file.rsplit(".", 1)[0] + ".svg"
        )

        cmd = [
            "vtracer.exe",  # If vtracer.exe is in the same folder
            "--input",
            input_path,
            "--output",
            output_path,
            "--hierarchical",
            "cutout",
            # "-f", "0",
            "-f",
            "0",
            "-p",
            "8",
            "-g",
            "12",
            "-m",
            "spline",
            "-l",
            "3.5",
            "-s",
            "0",
            # "-p", "8",
            # "-g", "12",
            # "-m", "spline",
            # "-l", "3.5"
        ]

        subprocess.run(cmd, check=True)
