import os
import shutil
import time
import argparse
from gradio_client import Client

# Initialize Hugging Face Gradio client
client = Client("https://carolineec-informativedrawings.hf.space/")


def process_single_image(input_path, output_name, output_dir="output"):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check if input image exists
    if not os.path.isfile(input_path):
        print(f"Input file does not exist: {input_path}")
        return 1  # error code

    try:
        print(f"Processing: {input_path}")
        start_time = time.time()

        # Call the Hugging Face endpoint
        result_path = client.predict(input_path, "style 1", api_name="/predict")

        if os.path.exists(result_path):
            output_path = os.path.join(output_dir, output_name)
            shutil.move(result_path, output_path)
            elapsed = time.time() - start_time
            print(f"Saved styled image to: {output_path}")
            print(f"Total time taken: {elapsed:.2f} seconds")
            return 0  # success
        else:
            print(f"Error: Output file not found - {result_path}")
            return 1

    except Exception as e:
        print(f"Processing failed: {e}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", required=True, help="Path to the input image")
    parser.add_argument("--output_name", required=True, help="Name for the output file")
    parser.add_argument(
        "--results_dir",
        required=False,
        default="output",
        help="Folder to store results",
    )

    args = parser.parse_args()

    exit_code = process_single_image(
        args.image_path, args.output_name, args.results_dir
    )
    exit(exit_code)
