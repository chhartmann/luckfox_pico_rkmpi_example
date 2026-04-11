#!/usr/bin/env python3
"""
Flask server for configuring YOLOv5 object detection on Luckfox Pico.
Allows users to configure:
- Confidence threshold
- NMS threshold  
- Enabled object classes
- Detection region of interest
"""

import os
import json
import threading
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuration file path (shared with C++ application)
CONFIG_FILE = "/tmp/yolov5_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "confidence_threshold": 0.25,
    "nms_threshold": 0.45,
    "enabled_classes": list(range(80)),  # All 80 COCO classes enabled by default
    "roi_enabled": False,
    "roi_x": 0,
    "roi_y": 0,
    "roi_width": 640,
    "roi_height": 480,
    "last_updated": None
}

# COCO class names (80 classes)
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
    "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

# In-memory configuration (will be synced with file)
current_config = DEFAULT_CONFIG.copy()


def load_config():
    """Load configuration from file if it exists."""
    global current_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                current_config.update(saved_config)
        except Exception as e:
            print(f"Error loading config: {e}")
            save_config()
    else:
        save_config()


def save_config():
    """Save current configuration to file."""
    global current_config
    current_config["last_updated"] = datetime.now().isoformat()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


@app.route('/')
def index():
    """Render the main configuration page."""
    return render_template('config.html', 
                         classes=COCO_CLASSES,
                         config=current_config)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    return jsonify({
        "success": True,
        "config": current_config,
        "classes": COCO_CLASSES
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    global current_config
    
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    # Update confidence threshold
    if "confidence_threshold" in data:
        try:
            conf = float(data["confidence_threshold"])
            if 0.01 <= conf <= 0.99:
                current_config["confidence_threshold"] = conf
            else:
                return jsonify({"success": False, "error": "Confidence threshold must be between 0.01 and 0.99"}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Invalid confidence threshold value"}), 400
    
    # Update NMS threshold
    if "nms_threshold" in data:
        try:
            nms = float(data["nms_threshold"])
            if 0.01 <= nms <= 0.99:
                current_config["nms_threshold"] = nms
            else:
                return jsonify({"success": False, "error": "NMS threshold must be between 0.01 and 0.99"}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Invalid NMS threshold value"}), 400
    
    # Update enabled classes
    if "enabled_classes" in data:
        try:
            enabled = data["enabled_classes"]
            if isinstance(enabled, list) and all(isinstance(x, int) and 0 <= x < 80 for x in enabled):
                current_config["enabled_classes"] = enabled
            else:
                return jsonify({"success": False, "error": "Invalid enabled classes format"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
    
    # Update ROI settings
    if "roi_enabled" in data:
        current_config["roi_enabled"] = bool(data["roi_enabled"])
    
    if "roi_x" in data:
        current_config["roi_x"] = int(data["roi_x"])
    
    if "roi_y" in data:
        current_config["roi_y"] = int(data["roi_y"])
    
    if "roi_width" in data:
        current_config["roi_width"] = int(data["roi_width"])
    
    if "roi_height" in data:
        current_config["roi_height"] = int(data["roi_height"])
    
    # Save configuration
    if save_config():
        return jsonify({
            "success": True,
            "message": "Configuration updated successfully",
            "config": current_config
        })
    else:
        return jsonify({"success": False, "error": "Failed to save configuration"}), 500


@app.route('/api/config/reset', methods=['POST'])
def reset_config():
    """Reset configuration to defaults."""
    global current_config
    current_config = DEFAULT_CONFIG.copy()
    if save_config():
        return jsonify({
            "success": True,
            "message": "Configuration reset to defaults",
            "config": current_config
        })
    else:
        return jsonify({"success": False, "error": "Failed to reset configuration"}), 500


@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get list of all available classes."""
    return jsonify({
        "success": True,
        "classes": COCO_CLASSES,
        "count": len(COCO_CLASSES)
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config_file": CONFIG_FILE,
        "config_exists": os.path.exists(CONFIG_FILE)
    })


if __name__ == '__main__':
    # Load existing configuration
    load_config()
    
    print("=" * 60)
    print("YOLOv5 Object Detection Configuration Server")
    print("=" * 60)
    print(f"Configuration file: {CONFIG_FILE}")
    print(f"Available classes: {len(COCO_CLASSES)}")
    print(f"Default confidence threshold: {DEFAULT_CONFIG['confidence_threshold']}")
    print(f"Default NMS threshold: {DEFAULT_CONFIG['nms_threshold']}")
    print("=" * 60)
    print("Starting Flask server on http://0.0.0.0:5000")
    print("=" * 60)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
