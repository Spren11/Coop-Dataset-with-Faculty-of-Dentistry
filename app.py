# app.py - Backend Server for Impacted Teeth Detection with YOLOv8

from flask import Flask, request, jsonify, send_file, render_template, redirect, send_from_directory
import os
from ultralytics import YOLO
import shutil  # Import shutil for moving files
from werkzeug.utils import secure_filename  # Import secure_filename for secure file paths
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-interactive plotting
from shapely.geometry import Point, Polygon

# Initialize Flask app
app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PREDICT_DIR = os.path.join(BASE_DIR, 'runs', 'pose', 'predict')
PLOTTED_DIR = os.path.join(BASE_DIR, 'plotted')
LABELS_FOLDER = os.path.join(BASE_DIR, 'labels')  # Add LABELS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(PREDICT_DIR, exist_ok=True)
os.makedirs(PLOTTED_DIR, exist_ok=True)
os.makedirs(LABELS_FOLDER, exist_ok=True)  # Create LABELS_FOLDER

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load pre-trained YOLO model
model = YOLO('best (1).pt')

# Function to move images from dynamically created predict folders to results folder
def move_images_to_results(selected_model):
    try:
        base_predict_dir = os.path.join(PREDICT_DIR, '..')  # Default for pose model
        if selected_model == "best (2).pt":
            base_predict_dir = os.path.join(BASE_DIR, 'runs', 'segment', 'predict')

        # Check if base directory exists
        if not os.path.exists(base_predict_dir):
            print(f"Directory {base_predict_dir} does not exist.")
            return False

        # Handle both subfolders and direct files
        predict_items = os.listdir(base_predict_dir)
        predict_folders = [d for d in predict_items if d.startswith('predict') and os.path.isdir(os.path.join(base_predict_dir, d))]
        
        # If no predict folders, process base directory directly
        if not predict_folders:
            predict_folders = ['']

        for folder in predict_folders:
            folder_path = os.path.join(base_predict_dir, folder)
            print(f"Processing path: {folder_path}")

            # Walk through all files in the path
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        src = os.path.join(root, file)
                        dest = os.path.join(RESULTS_DIR, file)
                        print(f"Moving {src} to {dest}")
                        try:
                            if os.path.exists(dest):
                                os.remove(dest)
                            shutil.move(src, dest)
                        except Exception as e:
                            print(f"Error moving file: {e}")

            # Only delete if it's a subfolder
            if folder:
                try:
                    shutil.rmtree(folder_path)
                    print(f"Deleted folder: {folder_path}")
                except Exception as e:
                    print(f"Error deleting folder: {e}")

        return True
    except Exception as e:
        print(f"Move error: {e}")
        return False

def calculate_distance_to_sector_border(r23_x, r23_y, sector_points):
    r23_point = Point(r23_x, r23_y)
    sector_polygon = Polygon(sector_points)
    return sector_polygon.exterior.distance(r23_point)

def process_image(image_file, label_file):
    img = mpimg.imread(image_file)

    with open(label_file, "r") as f:
        lines = f.readlines()

    labels, x_coords, y_coords = [], [], []
    for line in lines:
        parts = line.split()
        labels.append(parts[0])
        x_coords.append(float(parts[1]))
        y_coords.append(float(parts[2]))

    image_height, image_width = img.shape[:2]
    absolute_x = [x * image_width for x in x_coords]
    absolute_y = [y * image_height for y in y_coords]

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

    r23_index = labels.index("r23")
    r23_x, r23_y = absolute_x[r23_index], absolute_y[r23_index]

    m1_index = labels.index("m1")
    m1_x = absolute_x[m1_index]

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

    closest_sector = min(results, key=results.get)
    impact_type = {
        "Sector 1": "buccally impact",
        "Sector 2": "mid-alveolar",
        "Sector 3": "palatally impact"
    }.get(closest_sector, "Unknown")

    plt.figure(figsize=(10, 10))
    plt.imshow(img, cmap="gray")
    plt.scatter(absolute_x, absolute_y, color="red", s=30, label="Points")
    plt.scatter(r23_x, r23_y, color="green", s=50, label="r23")
    plt.text(r23_x, r23_y, "r23", color="white", fontsize=8, ha="center")  # Highlight r23

    # Plot flipped sectors
    for sector in sectors:
        r_start_x, r_start_y = 2 * m1_x - midpoints_x[sector["r_start"]], midpoints_y[sector["r_start"]]
        r_end_x, r_end_y = 2 * m1_x - midpoints_x[sector["r_end"]], midpoints_y[sector["r_end"]]
        c_start_x, c_start_y = 2 * m1_x - midpoints_x[sector["c_start"]], midpoints_y[sector["c_start"]]
        c_end_x, c_end_y = 2 * m1_x - midpoints_x[sector["c_end"]], midpoints_y[sector["c_end"]]

        flipped_sector_points = [(r_start_x, r_start_y), (c_start_x, c_start_y), (c_end_x, c_end_y), (r_end_x, r_end_y)]
        plt.fill([p[0] for p in flipped_sector_points], [p[1] for p in flipped_sector_points], alpha=0.2, label=f"{sector['label']} (Flipped)")

    plt.title(f"r23 is {impact_type}")
    plt.legend()
    plt.axis("off")

    output_file = os.path.join(PLOTTED_DIR, f"annotated_{os.path.splitext(os.path.basename(image_file))[0]}.jpg")
    plt.savefig(output_file, format="jpg", bbox_inches='tight', pad_inches=0, transparent=True)  # Save as .jpg
    plt.close()

    return output_file, impact_type, closest_sector

def process_images_and_labels():
    results = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            label_path = os.path.join(LABELS_FOLDER, filename.replace('.jpg', '.txt').replace('.png', '.txt'))

            if not os.path.exists(label_path):
                print(f"Skipping {filename} as no matching label found.")
                continue

            output_file, impact_type, closest_sector = process_image(image_path, label_path)

            results.append({
                "filename": os.path.basename(output_file),
                "impact_type": impact_type,
                "closest_sector": closest_sector
            })

    return results

# Define routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/edit.html')
def edit():
    return render_template('edit.html')

@app.route('/script.js')
def script():
    return send_from_directory('static', 'script.js')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        uploaded_files = request.files.getlist('files')
        if not uploaded_files:
            return jsonify({"error": "No file uploaded"}), 400

        selected_model = request.form.get("model", "best (1).pt")
        model = YOLO(selected_model)

        conf_threshold = 0.05 if selected_model == "best (2).pt" else 0.00005

        results = []
        for file in uploaded_files:
            if file.filename != '':
                # Ensure the file path is correctly formatted
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                labelpath = os.path.join(LABELS_FOLDER, filename.replace('.jpg', '.txt').replace('.png', '.txt'))

                print(f"Saving file to: {filepath}")  # Debugging statement
                file.save(filepath)

                # Debugging: Verify file path and contents
                if not os.path.exists(filepath):
                    print(f"Error: File not found after saving at {filepath}")
                    continue
                print(f"File saved at {filepath}")

                # Run model prediction and save in PREDICT_DIR
                try:
                    prediction_results = model.predict(
                        source=filepath,
                        imgsz=640,
                        conf=conf_threshold,
                        iou=0.5,
                        save=True,  # Save results
                        save_txt=True,  # Save results in text format
                        save_conf=False,
                        save_dir=PREDICT_DIR if selected_model == "best (1).pt" else os.path.join(BASE_DIR, 'runs', 'segment', 'predict'),  # Save results in the correct directory
                        device='cpu'  # Use CPU instead of GPU
                    )
                except Exception as e:
                    print(f"Error during prediction: {e}")
                    continue

                # Collect prediction data
                prediction_data = []
                for pred in prediction_results:
                    prediction_data.append({
                        "boxes": pred.boxes.xyxy.tolist() if pred.boxes else [],
                        "scores": pred.boxes.conf.tolist() if pred.boxes else [],
                        "labels": pred.boxes.cls.tolist() if pred.boxes else [],
                        "keypoints": pred.keypoints.data.tolist() if pred.keypoints else []
                    })

                # Append file-specific result
                result = {
                    "filename": filename,  # Retain the original filename
                    "prediction": prediction_data
                }
                results.append(result)

        # Move images from predict folder to results folder
        move_images_to_results(selected_model)

        return jsonify({"message": "Files processed successfully", "results": results}), 200

    except Exception as e:
        print(f"Error in /upload route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/results/<filename>', methods=['GET'])
def get_result_image(filename):
    try:
        # Check for both .jpg and .png extensions
        if filename.endswith('.png'):
            jpg_filename = filename.replace('.png', '.jpg')
            if os.path.exists(os.path.join(RESULTS_DIR, jpg_filename)):
                filename = jpg_filename
        elif filename.endswith('.jpg'):
            png_filename = filename.replace('.jpg', '.png')
            if os.path.exists(os.path.join(RESULTS_DIR, png_filename)):
                filename = png_filename
        print(f"Trying to serve image {filename}")
        return send_file(os.path.join(RESULTS_DIR, filename), mimetype='image/jpeg' if filename.endswith('.jpg') else 'image/png')
    except FileNotFoundError:
        print(f"Image {filename} not found in {RESULTS_DIR}")
        return jsonify({"error": "File not found"}), 404

@app.route('/plotted/<filename>', methods=['GET'])
def get_sector_image(filename):
    try:
        # Check for .jpg and fallback to .png
        filepath = os.path.join(PLOTTED_DIR, filename)
        if not os.path.exists(filepath):
            filepath = filepath.replace('.jpg', '.png')
        return send_file(filepath, mimetype='image/jpeg' if filepath.endswith('.jpg') else 'image/png')
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route('/process', methods=['POST'])
def process():
    try:
        results = process_images_and_labels()
        return jsonify({"message": "Images processed successfully", "results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)