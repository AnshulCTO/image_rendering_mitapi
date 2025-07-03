import os
import subprocess
import sys

filename = "sketches_bw"
input_folder = f"artwork_jpg_selected/{filename}"  # -sketch"
output_folder = f"input_svg/artwork_jpg_selected/{filename}"
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
            "--preset",
            "bw",
            "-f",
            "0",
            "-p",
            "8",
            "-g",
            "12",
            # "-m", "spline",
            "-l",
            "3.5",
            "-s",
            "0",
        ]

        subprocess.run(cmd, check=True)
