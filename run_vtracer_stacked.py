import os
import subprocess
import sys

filename = "225019fgsdl"
folder_name = "artworks_18_04_seg_selected"
input_folder = f"{folder_name}/{filename}-w"  # f"sam_outputs/{filename}"
output_folder = f"input_svg/{folder_name}/{filename}-w"
os.makedirs(output_folder, exist_ok=True)  # Ensure output directory exists

for file in os.listdir(input_folder):
    if file.lower().endswith((".png", ".jpg", ".jpeg")):
        input_path = os.path.join(input_folder, file)
        output_path = os.path.join(
            output_folder, "vtrace-" + file.rsplit(".", 1)[0] + ".svg"
        )
        print(output_path)
        cmd = [
            "vtracer.exe",  # If vtracer.exe is in the same folder
            "--input",
            input_path,
            "--output",
            output_path,
            "--hierarchical",
            "stacked",
            # "-f", "0",
            # "-f", "0",
            # "-p", "8",
            # "-g", "12",
            # "-m", "spline",
            # "-l", "3.5",
            # "-s", "0",
            # "-p", "8",
            # "-g", "12",
            # "-m", "spline",
            # "-l", "3.5"
        ]

        subprocess.run(cmd, check=True)
