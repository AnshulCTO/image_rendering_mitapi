import time
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import combine_svg
import subprocess
from PIL import Image
import numpy as np
import tempfile
import api_testing
from Sequence_generator_win_vtracer import process_single_file
from animate_inline import generate_animated_html

# Initialize the flask application
app = Flask(__name__)


def is_grayscale(image_path):
    with Image.open(image_path).convert("RGB") as img:
        arr = np.array(img)
    return np.allclose(arr[..., 0], arr[..., 1]) and np.allclose(
        arr[..., 1], arr[..., 2]
    )


@app.route("/api/is_grayscale", methods=["POST"])
def check_grayscale():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[-1]
    ) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = is_grayscale(tmp_path)
    finally:
        # Ensure image file is closed before deletion
        os.unlink(tmp_path)

    return jsonify({"is_grayscale": result})


@app.route("/")
def home():
    """
    home route that renders the main interface(index.html)
    This is the entry point of the application
    """
    return render_template("index_test.html")
    # return render_template("index.html")


@app.route("/render")
def render_page():
    file = request.args.get("file")
    mode = request.args.get("mode")
    return render_template("render.html", file=file, mode=mode)


@app.route("/api/thumbnails")
def get_thumbnails():
    """
    API endpoint to list the available thumbnail image files.
    Scans the /static/thumbnails directory and return a JSON list of images
    with .png, .jpg, .jpeg extensions
    """
    folder = os.path.join(app.static_folder, "thumbnails")

    # Filter for image files only
    files = [
        f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    return jsonify(files)


@app.route("/static/thumbnails/<filename>")
def serve_thumbnail(filename):
    """
    Route to serve individual thumbnail images from the static/thumbnails directory.
    This is useful if direct url access is needed for thumbnails
    """
    return send_from_directory(os.path.join(app.static_folder, "thumbnails"), filename)


@app.route("/api/convert_to_svg", methods=["POST"])
def convert_to_svg():
    start_time = time.time()
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Create a temporary file to hold the image
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[-1]
    ) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    # Prepare output SVG filename and path
    base_name = os.path.splitext(os.path.basename(file.filename))[0]
    output_folder = os.path.join("static", "svg_color")
    os.makedirs(output_folder, exist_ok=True)
    output_svg_name = f"{base_name}.svg"
    output_path = os.path.join(output_folder, output_svg_name)

    try:
        # Run vtracer
        subprocess.run(
            [
                "vtracer.exe",
                "--input",
                tmp_path,
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
                "-m",
                "spline",
                "-l",
                "3.5",
                "-s",
                "0",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        os.unlink(tmp_path)
        return jsonify({"error": f"vtracer failed: {str(e)}"}), 500
    finally:
        os.unlink(tmp_path)

    sequence_output_folder = os.path.join("static", "seq_svg_color")
    sequence_output_path = process_single_file(output_path, sequence_output_folder)
    if not sequence_output_path:
        return jsonify({"error": "Sequence generation failed"}), 500

    animate_color_output_folder = os.path.join("static", "animate_color_output")
    os.makedirs(animate_color_output_folder, exist_ok=True)
    animated_html_path = generate_animated_html(
        sequence_output_path, animate_color_output_folder
    )
    animated_html_url = (
        f"/static/animate_color_output/{os.path.basename(animated_html_path)}"
    )
    elapsed = time.time() - start_time
    print(f"Total time taken by this mode: {elapsed:.2f} seconds")
    return jsonify(
        {
            "success": True,
            "output_svg": f"/static/seq_svg_color/{os.path.basename(sequence_output_path)}",
            "animated_html": animated_html_url,
        }
    )


# sketch mode
@app.route("/api/convert_sketch_to_svg", methods=["POST"])
def convert_sketch_to_svg():
    start_time = time.time()
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Save the uploaded image temporarily
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[-1]
    ) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    base_name = os.path.splitext(os.path.basename(file.filename))[0]
    bw_path = os.path.join("static", "sketches", f"{base_name}.png")
    os.makedirs(os.path.dirname(bw_path), exist_ok=True)

    # Step 1: Check if grayscale

    # Step 2: Convert to BW
    try:
        image = Image.open(tmp_path).convert("L")
        bw_image = image.point(lambda p: 255 if p > 150 else 0)

        # Make white pixels transparent
        rgba_image = bw_image.convert("RGBA")
        datas = rgba_image.getdata()
        new_data = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                new_data.append((255, 255, 255, 0))  # Transparent white
            else:
                new_data.append(item)

        rgba_image.putdata(new_data)
        rgba_image.save(bw_path)
    except Exception as e:
        os.unlink(tmp_path)
        return jsonify({"error": f"Failed to convert to BW: {str(e)}"}), 500

    os.unlink(tmp_path)  # Clean up original temp file

    # Step 3: Vtracer SVG generation
    svg_output_path = os.path.join("static", "svg_sketch", f"{base_name}.svg")
    os.makedirs(os.path.dirname(svg_output_path), exist_ok=True)

    try:
        subprocess.run(
            [
                "vtracer.exe",
                "--input",
                bw_path,
                "--output",
                svg_output_path,
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
                "-l",
                "3.5",
                "-s",
                "0",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"vtracer failed: {str(e)}"}), 500

    # Step 4: Sequence generation
    sequence_output_folder = os.path.join("static", "seq_svg_sketch")
    os.makedirs(sequence_output_folder, exist_ok=True)
    sequence_output_path = process_single_file(svg_output_path, sequence_output_folder)

    if not sequence_output_path:
        return jsonify({"error": "Sequence generation failed"}), 500

    # Step 5: Animate inline
    animate_sketch_output_folder = os.path.join("static", "animate_sketch_output")
    os.makedirs(animate_sketch_output_folder, exist_ok=True)
    animated_html_path = generate_animated_html(
        sequence_output_path, animate_sketch_output_folder
    )
    animated_html_url = (
        f"/static/animate_sketch_output/{os.path.basename(animated_html_path)}"
    )
    elapsed = time.time() - start_time
    print(f"Total time taken by this mode: {elapsed:.2f} seconds")
    return jsonify(
        {
            "success": True,
            "output_svg": f"/static/seq_svg_sketch/{os.path.basename(sequence_output_path)}",
            "animated_html": animated_html_url,
        }
    )


@app.route("/api/convert_color_to_sketch_to_svg", methods=["POST"])
def convert_color_to_sketch_to_svg():
    start_time = time.time()
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Save the uploaded image temporarily
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[-1]
    ) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    base_name = os.path.splitext(os.path.basename(file.filename))[0]

    original_width, original_height = None, None
    try:
        with Image.open(tmp_path) as img:
            original_width, original_height = img.size
            print(
                f"Input image dimensions (original): Width={original_width}, Height={original_height}"
            )
    except Exception as e:
        os.unlink(tmp_path)
        return (
            jsonify({"error": f"Could not read original image dimensions: {str(e)}"}),
            500,
        )
    try:
        mit_api_output_folder = os.path.join("static", "mit_api_sketch_output")
        os.makedirs(mit_api_output_folder, exist_ok=True)

        script_path = os.path.abspath("api_testing.py")
        command = [
            "python",
            "-u",
            script_path,
            "--image_path",
            tmp_path,
            "--output_name",
            f"{base_name}.png",
            "--results_dir",
            mit_api_output_folder,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        print("ML STDOUT:", result.stdout)
        print("ML STDERR:", result.stderr)
        print(base_name)

        if result.returncode != 0:
            return jsonify({"error": "ML script failed", "details": result.stderr}), 500

        model_output_path = os.path.join(mit_api_output_folder, f"{base_name}.png")
        bw_path = os.path.join("static", "sketches", f"{base_name}.png")
        os.makedirs(os.path.dirname(bw_path), exist_ok=True)

        image = Image.open(model_output_path).convert("L")
        print(
            f"ML script output image dimensions: Width={image.width}, Height={image.height}"
        )

        # Resize to original dimensions if needed
        if (
            original_width
            and original_height
            and (image.width, image.height) != (original_width, original_height)
        ):
            image = image.resize(
                (original_width, original_height), Image.Resampling.LANCZOS
            )
            print(
                f"Resized ML output to original dimensions: Width={image.width}, Height={image.height}"
            )

        bw_image = image.point(lambda p: 255 if p > 150 else 0)
        bw_image.save(bw_path)

        sketch_svg_path = os.path.join("static", "svg_sketch", f"{base_name}.svg")
        os.makedirs(os.path.dirname(sketch_svg_path), exist_ok=True)

        subprocess.run(
            [
                "vtracer.exe",
                "--input",
                bw_path,
                "--output",
                sketch_svg_path,
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
                "-l",
                "3.5",
                "-s",
                "0",
            ],
            check=True,
        )

        sketch_seq_folder = os.path.join("static", "seq_svg_sketch")
        os.makedirs(sketch_seq_folder, exist_ok=True)
        sketch_seq_svg = process_single_file(sketch_svg_path, sketch_seq_folder)
        if not sketch_seq_svg:
            return jsonify({"error": "Sequence generation failed"}), 500

        animate_sketch_output_folder = os.path.join("static", "animate_sketch_output")
        os.makedirs(animate_sketch_output_folder, exist_ok=True)
        animated_html_path = generate_animated_html(
            sketch_seq_svg, animate_sketch_output_folder
        )
        animated_html_url = (
            f"/static/animate_sketch_output/{os.path.basename(animated_html_path)}"
        )
        elapsed = time.time() - start_time
        print(f"Total time taken by this mode: {elapsed:.2f} seconds")
        return jsonify(
            {
                "success": True,
                "output_svg": f"/static/seq_svg_sketch/{os.path.basename(sketch_seq_svg)}",
                "animated_html": animated_html_url,
            }
        )

    except Exception as e:
        return (
            jsonify(
                {"error": "Error during sketch conversion pipeline", "details": str(e)}
            ),
            500,
        )


# Layered
@app.route("/api/convert_layered_to_svg", methods=["POST"])
def convert_layered_to_svg():
    start_time = time.time()
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Create a temporary file to hold the image
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[-1]
    ) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    # Prepare output SVG filename and path
    base_name = os.path.splitext(os.path.basename(file.filename))[0]
    output_folder = os.path.join("static", "svg_layered")
    os.makedirs(output_folder, exist_ok=True)
    output_svg_name = f"{base_name}.svg"
    output_path = os.path.join(output_folder, output_svg_name)

    try:
        # Run vtracer
        subprocess.run(
            [
                "vtracer.exe",  # If vtracer.exe is in the same folder
                "--input",
                tmp_path,
                "--output",
                output_path,
                "--hierarchical",
                "stacked",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        os.unlink(tmp_path)
        return jsonify({"error": f"vtracer failed: {str(e)}"}), 500
    finally:
        os.unlink(tmp_path)

    # sequence_output_folder = os.path.join("static", "svg_output")
    # sequence_output_path = process_single_file(output_path, sequence_output_folder)
    # if not sequence_output_path:
    #     return jsonify({"error": "Sequence generation failed"}), 500

    animate_layered_output_folder = os.path.join("static", "animate_layered_output")
    os.makedirs(animate_layered_output_folder, exist_ok=True)
    animated_html_path = generate_animated_html(
        output_path, animate_layered_output_folder
    )
    animated_html_url = (
        f"/static/animate_layered_output/{os.path.basename(animated_html_path)}"
    )
    elapsed = time.time() - start_time
    print(f"Total time taken by this mode: {elapsed:.2f} seconds")
    return jsonify(
        {
            "success": True,
            "output_svg": f"/static/svg_layered/{os.path.basename(output_path)}",
            "animated_html": animated_html_url,
        }
    )


@app.route("/api/convert_sketchNpaint_to_svg", methods=["POST"])
def convert_sketchNpaint_to_svg():
    start_time = time.time()
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Save uploaded image to a temp file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[-1]
    ) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    base_name = os.path.splitext(os.path.basename(file.filename))[0]

    original_width, original_height = None, None
    try:
        with Image.open(tmp_path) as img:
            original_width, original_height = img.size
            print(
                f"Input image dimensions (original): Width={original_width}, Height={original_height}"
            )
    except Exception as e:
        os.unlink(tmp_path)
        return (
            jsonify({"error": f"Could not read original image dimensions: {str(e)}"}),
            500,
        )

    ####### --- PAINT MODE --- #######
    try:
        paint_svg_path = os.path.join(
            "static", "svg_sNp_paint", f"{base_name}_paint.svg"
        )
        os.makedirs(os.path.dirname(paint_svg_path), exist_ok=True)

        subprocess.run(
            [
                "vtracer.exe",
                "--input",
                tmp_path,
                "--output",
                paint_svg_path,
                "--hierarchical",
                "cutout",
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
            ],
            check=True,
        )

        paint_seq_folder = os.path.join("static", "seq_sNp_svg_paint")
        os.makedirs(paint_seq_folder, exist_ok=True)
        paint_seq_svg = process_single_file(paint_svg_path, paint_seq_folder)
        if not paint_seq_svg:
            return jsonify({"error": "Sequence generation failed for paint part"}), 500

    except subprocess.CalledProcessError as e:
        os.unlink(tmp_path)
        return jsonify({"error": f"Paint Vtracer failed: {str(e)}"}), 500

    ####### --- SKETCH MODE --- #######
    try:
        mit_output_folder = os.path.join("static", "mit__api_snp_sketch_output")
        os.makedirs(mit_output_folder, exist_ok=True)

        script_path = os.path.abspath("api_testing.py")
        command = [
            "python",
            "-u",
            script_path,
            "--image_path",
            tmp_path,
            "--output_name",
            f"{base_name}.png",
            "--results_dir",
            mit_output_folder,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        print("ML STDOUT:", result.stdout)
        print("ML STDERR:", result.stderr)
        print(base_name)

        if result.returncode != 0:
            return jsonify({"error": "ML script failed", "details": result.stderr}), 500

        model_output_path = os.path.join(mit_output_folder, f"{base_name}.png")
        bw_path = os.path.join("static", "sNp_sketches", f"{base_name}.png")
        os.makedirs(os.path.dirname(bw_path), exist_ok=True)

        image = Image.open(model_output_path).convert("L")
        print(
            f"ML script output image dimensions: Width={image.width}, Height={image.height}"
        )

        # Resize the ML output image back to the original dimensions
        if (
            original_width
            and original_height
            and (image.width, image.height) != (original_width, original_height)
        ):
            image = image.resize(
                (original_width, original_height), Image.Resampling.LANCZOS
            )
            print(
                f"Resized ML output to original dimensions: Width={image.width}, Height={image.height}"
            )

        bw_image = image.point(lambda p: 255 if p > 150 else 0)
        bw_image.save(bw_path)

        sketch_svg_path = os.path.join(
            "static", "svg_sNp_sketch", f"{base_name}_sketch.svg"
        )
        os.makedirs(os.path.dirname(sketch_svg_path), exist_ok=True)

        subprocess.run(
            [
                "vtracer.exe",
                "--input",
                bw_path,
                "--output",
                sketch_svg_path,
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
                "-l",
                "3.5",
                "-s",
                "0",
            ],
            check=True,
        )

        sketch_seq_folder = os.path.join("static", "seq_sNp_svg_sketch")
        os.makedirs(sketch_seq_folder, exist_ok=True)
        sketch_seq_svg = process_single_file(sketch_svg_path, sketch_seq_folder)
        combined_svg_folder = "static\combined_seq_svg_sNp"
        os.makedirs(combined_svg_folder, exist_ok=True)
        combined_svg_file = combine_svg.process_svg_pair(
            f"sequence-{base_name}",
            os.path.join("static", "seq_sNp_svg_paint"),
            os.path.join("static", "seq_sNp_svg_sketch"),
            combined_svg_folder,
        )
        if not sketch_seq_svg:
            return jsonify({"error": "Sequence generation failed for sketch part"}), 500

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Sketch Vtracer failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Sketch processing error: {str(e)}"}), 500

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Step 5: Animate inline
    animate_sketch_output_folder = os.path.join("static", "animate_sNp_output")
    os.makedirs(animate_sketch_output_folder, exist_ok=True)
    animated_html_path = generate_animated_html(
        combined_svg_file, animate_sketch_output_folder
    )
    animated_html_url = (
        f"/static/animate_sNp_output/{os.path.basename(animated_html_path)}"
    )
    elapsed = time.time() - start_time
    print(f"Total time taken by this mode: {elapsed:.2f} seconds")
    return jsonify(
        {
            "success": True,
            "output_svg": f"/static/combined_seq_svg_sNp/{os.path.basename(combined_svg_file)}",
            "animated_html": animated_html_url,
        }
    )


@app.route("/api/log_mode", methods=["POST"])
def log_mode():
    data = request.get_json()
    mode = data.get("mode")
    print(f"🟢 Mode selected from frontend: {mode}")
    return jsonify({"status": "logged"}), 200


if __name__ == "__main__":
    # Run the app in debug mode for development
    app.run(debug=True)  # (debug=True, port=5002) running multiple flask apps
