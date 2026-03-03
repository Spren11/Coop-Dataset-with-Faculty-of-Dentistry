import os
import json
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file, render_template, redirect, send_from_directory
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from shapely.geometry import Point, Polygon

# Initialize Flask app
app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
LABELS_FOLDER = os.path.join(BASE_DIR, 'labels')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTTED_DIR = os.path.join(BASE_DIR, "plotted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LABELS_FOLDER, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(PLOTTED_DIR, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def calculate_distance_to_sector_border(r23_x, r23_y, sector_points):
    r23_point = Point(r23_x, r23_y)
    sector_polygon = Polygon(sector_points)
    return sector_polygon.exterior.distance(r23_point)

def process_image(image_file, label_file):
    # Load the X-ray image
    img = mpimg.imread(image_file)

    # Load and parse the label data
    with open(label_file, "r") as f:
        lines = f.readlines()

    labels, x_coords, y_coords = [], [], []
    for line in lines:
        parts = line.split()
        labels.append(parts[0])
        x_coords.append(float(parts[1]))
        y_coords.append(float(parts[2]))

    # Convert coordinates to absolute dimensions
    image_height, image_width = img.shape[:2]
    absolute_x = [x * image_width for x in x_coords]
    absolute_y = [y * image_height for y in y_coords]

    # Define sectors and midpoints
    pairs = [("c11", "c12"), ("c12", "c13"), ("c13", "c14"), ("c14", "c15"),
             ("r11", "r12"), ("r12", "r13"), ("r13", "r14"), ("r14", "r15")]
    midpoints_x = {}
    midpoints_y = {}
    for pair in pairs:
        index1 = labels.index(pair[0])
        index2 = labels.index(pair[1])
        midpoints_x[pair] = (absolute_x[index1] + absolute_x[index2]) / 2
        midpoints_y[pair] = (absolute_y[index1] + absolute_y[index2]) / 2

    sectors = [
        {"r_start": ("r11", "r12"), "r_end": ("r12", "r13"), "c_start": ("c11", "c12"), "c_end": ("c12", "c13"), "label": "Sector 1"},
        {"r_start": ("r12", "r13"), "r_end": ("r13", "r14"), "c_start": ("c12", "c13"), "c_end": ("c13", "c14"), "label": "Sector 2"},
        {"r_start": ("r13", "r14"), "r_end": ("r14", "r15"), "c_start": ("c13", "c14"), "c_end": ("c14", "c15"), "label": "Sector 3"},
    ]

    # Get r23 coordinates
    r23_index = labels.index("r23")
    r23_x, r23_y = absolute_x[r23_index], absolute_y[r23_index]

    # Get m1 position for flipping
    m1_index = labels.index("m1")
    m1_x = absolute_x[m1_index]

    # Calculate distances
    results = {}
    for sector in sectors:
        r_start_x = 2 * m1_x - midpoints_x[sector["r_start"]]
        r_start_y = midpoints_y[sector["r_start"]]
        r_end_x = 2 * m1_x - midpoints_x[sector["r_end"]]
        r_end_y = midpoints_y[sector["r_end"]]
        c_start_x = 2 * m1_x - midpoints_x[sector["c_start"]]
        c_start_y = midpoints_y[sector["c_start"]]
        c_end_x = 2 * m1_x - midpoints_x[sector["c_end"]]
        c_end_y = midpoints_y[sector["c_end"]]

        flipped_sector_points = [(r_start_x, r_start_y), (c_start_x, c_start_y), (c_end_x, c_end_y), (r_end_x, r_end_y)]
        results[sector["label"]] = calculate_distance_to_sector_border(r23_x, r23_y, flipped_sector_points)

    # Determine closest sector and impact type
    closest_sector = min(results, key=results.get)
    impact_type = {
        "Sector 1": "buccally impact",
        "Sector 2": "mid-alveolar",
        "Sector 3": "palatally impact"
    }.get(closest_sector, "Unknown")

    # Plot the results
    plt.figure(figsize=(10, 10))
    plt.imshow(img, cmap="gray")
    plt.scatter(absolute_x, absolute_y, color="red", s=30, label="Points")
    plt.scatter(r23_x, r23_y, color="green", s=50, label="r23")
    plt.title(f"r23 is {impact_type}")
    plt.legend()
    plt.axis("off")

    # Save the plotted image
    output_file = os.path.join(PLOTTED_DIR, f"annotated_{os.path.basename(image_file).replace('.png', '.jpg')}")
    plt.savefig(output_file)
    plt.close()

    return output_file, impact_type, closest_sector

# Function to process images and labels
def process_images_and_labels():
    results = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            label_path = os.path.join(LABELS_FOLDER, filename.replace('.jpg', '.txt').replace('.png', '.txt'))

            if not os.path.exists(label_path):
                raise Exception(f"Label file not found for {filename}")

            # Process the image and label
            output_file, impact_type, closest_sector = process_image(image_path, label_path)

            # Append results for web display
            results.append({
                "filename": os.path.basename(output_file),
                "impact_type": impact_type,
                "closest_sector": closest_sector
            })

    return results

@app.route('/process', methods=['POST'])
def process():
    try:
        results = process_images_and_labels()
        return jsonify({"message": "Images processed successfully", "results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
