# YOLOv5 Object Detection Configuration Server

A Flask-based web interface for configuring YOLOv5 object detection parameters on Luckfox Pico boards.

## Features

- **Confidence Threshold**: Adjust the minimum confidence score for detected objects (0.01 - 0.99)
- **NMS Threshold**: Configure non-maximum suppression to filter duplicate detections
- **Class Selection**: Enable/disable specific COCO object classes (80 classes available)
- **Region of Interest (ROI)**: Define a specific area for object detection
- **Real-time Configuration**: Changes are saved immediately and can be read by the C++ application
- **Responsive Web UI**: Modern, mobile-friendly interface

## Installation

### Prerequisites

```bash
pip install flask
```

### Running the Server

```bash
cd /workspace/example/luckfox_pico_rtsp_yolov5
python3 flask_server.py
```

The server will start on `http://0.0.0.0:5000`

## Usage

### Web Interface

1. Open your browser and navigate to `http://<device-ip>:5000`
2. Adjust the detection thresholds using the sliders
3. Select which object classes to detect
4. Optionally configure a region of interest
5. Click "Save Configuration" to apply changes

### API Endpoints

#### Get Current Configuration
```bash
curl http://localhost:5000/api/config
```

#### Update Configuration
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "confidence_threshold": 0.5,
    "nms_threshold": 0.4,
    "enabled_classes": [0, 2, 15, 16],
    "roi_enabled": false
  }'
```

#### Reset to Defaults
```bash
curl -X POST http://localhost:5000/api/config/reset
```

#### Health Check
```bash
curl http://localhost:5000/health
```

## Configuration File

The server saves configuration to `/tmp/yolov5_config.json`:

```json
{
  "confidence_threshold": 0.25,
  "nms_threshold": 0.45,
  "enabled_classes": [0, 1, 2, ...],
  "roi_enabled": false,
  "roi_x": 0,
  "roi_y": 0,
  "roi_width": 640,
  "roi_height": 480,
  "last_updated": "2024-01-01T12:00:00"
}
```

## Integration with C++ Application

To integrate this configuration system with the YOLOv5 C++ application:

### Option 1: Read Configuration File

Add code to read the JSON configuration file before or during inference:

```cpp
#include <fstream>
#include <json/json.h>  // or any JSON library

bool loadConfig(float& confThreshold, float& nmsThreshold) {
    std::ifstream configFile("/tmp/yolov5_config.json");
    if (!configFile.is_open()) {
        return false;
    }
    
    Json::Value root;
    configFile >> root;
    
    confThreshold = root["confidence_threshold"].asFloat();
    nmsThreshold = root["nms_threshold"].asFloat();
    
    // Update enabled classes
    // ...
    
    return true;
}
```

Then modify the `inference_yolov5_model` function to use these values:

```cpp
int inference_yolov5_model(rknn_app_context_t *app_ctx, 
                           object_detect_result_list *od_results,
                           float conf_threshold,
                           float nms_threshold) {
    // Use the provided thresholds instead of hardcoded values
    post_process(app_ctx, app_ctx->output_mems, 
                 conf_threshold, nms_threshold, od_results);
}
```

### Option 2: Watch for Configuration Changes

Use a file watcher or poll the configuration file periodically:

```cpp
#include <sys/inotify.h>

void watchConfigFile() {
    int fd = inotify_init();
    int wd = inotify_add_watch(fd, "/tmp/yolov5_config.json", IN_MODIFY);
    
    while (true) {
        struct inotify_event event;
        read(fd, &event, sizeof(event));
        
        if (event.mask & IN_MODIFY) {
            // Reload configuration
            loadConfig(confThreshold, nmsThreshold);
            printf("Configuration updated!\n");
        }
    }
}
```

### Option 3: HTTP Client in C++

Make HTTP requests directly from the C++ application:

```cpp
#include <curl/curl.h>

std::string getConfigFromServer() {
    CURL *curl;
    CURLcode res;
    std::string readBuffer;
    
    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, "http://localhost:5000/api/config");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }
    
    return readBuffer;
}
```

## COCO Classes Reference

The 80 COCO classes available for detection:

| ID | Class | ID | Class |
|----|-------|----|-------|
| 0 | person | 40 | bottle |
| 1 | bicycle | 41 | wine glass |
| 2 | car | 42 | cup |
| 3 | motorcycle | 43 | fork |
| 4 | airplane | 44 | knife |
| 5 | bus | 45 | spoon |
| 6 | train | 46 | bowl |
| 7 | truck | 47 | banana |
| 8 | boat | 48 | apple |
| ... | ... | ... | ... |

Full list available in `flask_server.py`.

## Quick Presets

### High Precision (Fewer False Positives)
- Confidence: 0.6
- NMS: 0.3
- Classes: person, car, dog, cat only

### High Sensitivity (Detect More Objects)
- Confidence: 0.15
- NMS: 0.5
- Classes: All enabled

### Balanced (Default)
- Confidence: 0.25
- NMS: 0.45
- Classes: Common objects only

## Troubleshooting

### Server Won't Start
```bash
# Check if port 5000 is already in use
netstat -tulpn | grep 5000

# Kill existing process if needed
kill -9 $(lsof -t -i:5000)
```

### Configuration Not Saving
```bash
# Check permissions on /tmp directory
ls -la /tmp/yolov5_config.json

# Ensure write permissions
chmod 666 /tmp/yolov5_config.json
```

### C++ Application Not Reading Config
```bash
# Verify config file exists
cat /tmp/yolov5_config.json

# Check file format
python3 -m json.tool /tmp/yolov5_config.json
```

## Performance Considerations

- The Flask server runs independently from the C++ inference application
- Configuration changes take effect on next inference cycle
- For real-time updates, implement file watching in the C++ application
- Keep the number of enabled classes reasonable for best performance

## Security Notes

⚠️ **Warning**: This server has no authentication. Only expose it on trusted networks.

For production use:
- Add authentication middleware
- Use HTTPS
- Restrict access by IP
- Run behind a reverse proxy (nginx, Apache)

## License

This configuration server is provided as part of the Luckfox Pico RTSP examples.
