import os
import sys
import os
import sys
import re
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist

# Precompile the regular expression for efficiency
NUMERIC_REGEX = re.compile(r"[-+]?\d*\.\d+|\d+")


def extract_fill_colour(style):
    match = re.search(r"fill:\s*([^;]+)", style)
    if match:
        return match.group(1)
    return None


# def parse_transform(transform):
#     """Extract translate(x, y) values from transform attribute."""
#     if not transform:
#         return 0, 0  # Default if no transform provided

#     match = re.search(r'translate\((-?\d+\.?\d*)(?:,\s*(-?\d+\.?\d*))?\)', transform)
#     if match:
#         x = float(match.group(1))
#         y = float(match.group(2)) if match.group(2) else 0.0  # Default y to 0 if missing
#         return x, y
#     return 0, 0  # Default if no match found
import re


def parse_transform(transform):
    """Extract translate(x, y) values from transform attribute."""
    if not transform:
        return 0.0, 0.0  # Default if no transform provided

    # Updated regex to handle cases where Y is explicitly given as 0 (e.g., "translate(986,0)")
    match = re.search(r"translate\((-?\d+\.?\d*),\s*(-?\d+\.?\d*|0)\)", transform)
    if match:
        x = float(match.group(1))
        y = (
            float(match.group(2)) if match.group(2) is not None else 0.0
        )  # Explicitly check for None
        return x, y

    # Handle cases where only X is given (e.g., "translate(986)")
    match = re.search(r"translate\((-?\d+\.?\d*)\)", transform)
    if match:
        x = float(match.group(1))
        return x, 0.0  # Default Y to 0.0

    return 0.0, 0.0  # Default if no match found


def parse_dimension(value):
    return float(value.replace("px", "").strip()) if "px" in value else float(value)


def extract_numeric_values(s):
    """Extract numeric values from a string using a precompiled regex."""
    return NUMERIC_REGEX.findall(s)


def parse_svg(svg_file):
    """Parse SVG file and extract relevant path data efficiently."""
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Extract viewBox and parse width and height
    view_box = root.get("viewBox")
    if view_box:
        _, _, svg_width, svg_height = map(float, view_box.split())
    else:
        # Fallback if viewBox is not present
        svg_width = parse_dimension(root.get("width", "1000"))
        svg_height = parse_dimension(root.get("height", "1000"))
        # svg_width = float(root.get('width', '1000'))
        # svg_height = float(root.get('height', '1000'))

    # Namespace handling to avoid repeated namespace strings
    namespaces = {"svg": "http://www.w3.org/2000/svg"}

    # Initialize lists to collect path attributes
    path_datas = []
    fills = []
    x_values = []
    y_values = []
    path_lengths = []
    transforms = []

    # Iterate through path elements using efficient list extraction
    for path_elem in root.findall(".//svg:path", namespaces):
        path_data = path_elem.get("d", "")
        # fill = path_elem.get('fill', '')
        transform = path_elem.get("transform")
        # print(transform)
        # print(Jp)
        # style = path_elem.get('style')
        fill_colour = path_elem.get("fill")
        # fill_colour = extract_fill_colour(style)
        # Extract numeric values
        numeric_values = extract_numeric_values(path_data)

        # Safely extract X and Y values
        # M_x = numeric_values[0] if len(numeric_values) >= 1 else None
        # M_y = numeric_values[1] if len(numeric_values) >= 2 else None
        M_x, M_y = parse_transform(transform)
        # print(M_x, M_y)
        # print(jp)
        # Calculate the length of the path data
        path_length = len(path_data)

        # Append to lists
        path_datas.append(path_data)
        transforms.append(transform)
        # fills.append(fill)
        fills.append(fill_colour)
        x_values.append(float(M_x))  # if M_x else None)
        y_values.append(float(M_y))  # if M_y else None)
        path_lengths.append(path_length)

    # Create DataFrame using collected lists
    df = pd.DataFrame(
        {
            "fill": fills,
            "transform": transforms,
            "X_value": x_values,
            "Y_value": y_values,
            "path_length": path_lengths,
            "width": svg_width,
            "height": svg_height,
            "path_data": path_datas,
        }
    )

    # Sort DataFrame based on 'path_length' in descending order
    df.sort_values(by="path_length", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.to_csv("output.csv", index=False)
    return df


def hierarchical_clustering(df, file_name, max_distance=100):
    """Perform hierarchical clustering on the DataFrame and plot the results."""
    # Drop rows with missing X or Y values to avoid errors in clustering
    # Remove Missing Values
    # df_clean = df.dropna(subset=['X_value', 'Y_value'])
    df_clean = df
    # # Shift to Non-Negative (if required)
    # min_x, min_y = df_clean['X_value'].min(), df_clean['Y_value'].min()
    # if min_x < 0:
    #     df_clean['X_value'] -= min_x
    # if min_y < 0:
    #     df_clean['Y_value'] -= min_y

    # # **Check If There Are Enough Valid Points**
    # if len(df_clean) < 2:
    #     raise ValueError("Not enough valid points for clustering. Ensure at least two non-missing, non-identical points.")

    # Compute Pairwise Distances
    distances = pdist(df_clean[["X_value", "Y_value"]])

    # **Ensure Distance Matrix is Not Empty**
    # if distances.size == 0:
    #     raise ValueError("Distance matrix is empty. Check if all remaining points are identical.")

    linkage_matrix = linkage(distances, method="ward")

    # Form clusters based on the maximum distance
    clusters = fcluster(linkage_matrix, t=max_distance, criterion="distance")
    df_clean["Cluster"] = clusters
    # df_clean.to_csv(f'{file_name}.csv', index=False)
    df_sorted = df_clean.sort_values(by="Cluster")
    # df_sorted = df_clean.sort_values(by=['Cluster', 'path_length'])
    num_clusters = df_sorted["Cluster"].nunique()
    print(f"Number of clusters: {num_clusters}")
    return df_sorted


def dataframe_to_svg(df, svg_file_path):
    """Generate an SVG file from the DataFrame containing path data."""
    if df.empty:
        print("DataFrame is empty. No SVG will be generated.")
        return

    # Get the width and height from the first row
    width = df["width"].iloc[0]
    height = df["height"].iloc[0]

    # Start building the SVG content
    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">\n'
    ]

    # Efficiently concatenate path elements
    svg_elements.extend(
        [
            f'  <path d="{path_data}" transform ="{transform}" fill="{fill_color}" />\n'
            for path_data, transform, fill_color in zip(
                df["path_data"], df["transform"], df["fill"]
            )
        ]
    )

    # Close the SVG tag
    svg_elements.append("</svg>")

    # Write the SVG content to the file
    with open(svg_file_path, "w") as svg_file:
        svg_file.writelines(svg_elements)


def process_folder(parent_input_folder, parent_output_folder):
    """Process all SVG files in subfolders and save outputs in the corresponding output subfolders."""

    for subfolder in os.listdir(parent_input_folder):
        subfolder_path = os.path.join(parent_input_folder, subfolder)

        # Ensure it's a directory before processing
        if os.path.isdir(subfolder_path):
            output_subfolder = os.path.join(parent_output_folder, subfolder)
            os.makedirs(output_subfolder, exist_ok=True)  # Create output subfolder

            # Process SVG files in the current subfolder
            for file_name in os.listdir(subfolder_path):
                if file_name.endswith(".svg"):
                    svg_file_path = os.path.join(subfolder_path, file_name)
                    print(f"Processing file: {svg_file_path}")

                    df = parse_svg(svg_file_path)
                    if len(df) > 40000:
                        print("Large file, cannot process")
                        continue

                    base_file_name = os.path.splitext(file_name)[0]
                    output_svg_path = os.path.join(
                        output_subfolder, f"sequence-{base_file_name}.svg"
                    )
                    print(len(df))

                    dist = int(len(df) / 100)

                    if len(df) > 2:
                        df_combined = hierarchical_clustering(
                            df, file_name, max_distance=dist
                        )
                        dataframe_to_svg(df_combined, output_svg_path)
                    else:
                        dataframe_to_svg(df, output_svg_path)

                    print(f"Saved output SVG to: {output_svg_path}")


if __name__ == "__main__":
    # Check if the right number of arguments are passed
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    # Call the function to process all SVG files in the input folder
    process_folder(input_folder, output_folder)
