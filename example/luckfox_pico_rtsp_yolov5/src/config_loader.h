// config_loader.h
// Header file for loading YOLOv5 configuration from Flask server JSON file

#ifndef __CONFIG_LOADER_H
#define __CONFIG_LOADER_H

#include <string>
#include <vector>
#include <fstream>
#include <sstream>

// Simple JSON parsing without external dependencies
class YoloConfig {
public:
    float confidence_threshold;
    float nms_threshold;
    std::vector<int> enabled_classes;
    bool roi_enabled;
    int roi_x;
    int roi_y;
    int roi_width;
    int roi_height;
    std::string last_updated;

    YoloConfig() : 
        confidence_threshold(0.25f),
        nms_threshold(0.45f),
        roi_enabled(false),
        roi_x(0),
        roi_y(0),
        roi_width(640),
        roi_height(480) {
        // Enable all classes by default
        for (int i = 0; i < 80; i++) {
            enabled_classes.push_back(i);
        }
    }
};

// Parse a simple JSON value (basic implementation)
static std::string extractStringValue(const std::string& json, const std::string& key) {
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return "";
    
    pos = json.find(":", pos);
    if (pos == std::string::npos) return "";
    
    pos = json.find("\"", pos);
    if (pos == std::string::npos) return "";
    
    size_t endPos = json.find("\"", pos + 1);
    if (endPos == std::string::npos) return "";
    
    return json.substr(pos + 1, endPos - pos - 1);
}

static float extractFloatValue(const std::string& json, const std::string& key) {
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return 0.0f;
    
    pos = json.find(":", pos);
    if (pos == std::string::npos) return 0.0f;
    
    // Skip whitespace
    pos++;
    while (pos < json.size() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
    
    // Extract number
    size_t endPos = pos;
    while (endPos < json.size() && (isdigit(json[endPos]) || json[endPos] == '.')) endPos++;
    
    if (endPos == pos) return 0.0f;
    
    return std::stof(json.substr(pos, endPos - pos));
}

static bool extractBoolValue(const std::string& json, const std::string& key) {
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return false;
    
    pos = json.find(":", pos);
    if (pos == std::string::npos) return false;
    
    return json.find("true", pos) < json.find(",", pos);
}

static std::vector<int> extractIntArray(const std::string& json, const std::string& key) {
    std::vector<int> result;
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return result;
    
    pos = json.find("[", pos);
    if (pos == std::string::npos) return result;
    
    size_t endPos = json.find("]", pos);
    if (endPos == std::string::npos) return result;
    
    std::string arrayStr = json.substr(pos + 1, endPos - pos - 1);
    
    std::stringstream ss(arrayStr);
    std::string item;
    while (std::getline(ss, item, ',')) {
        // Trim whitespace
        size_t start = item.find_first_not_of(" \t\n\r");
        size_t end = item.find_last_not_of(" \t\n\r");
        if (start != std::string::npos && end != std::string::npos) {
            try {
                result.push_back(std::stoi(item.substr(start, end - start + 1)));
            } catch (...) {
                // Ignore parse errors
            }
        }
    }
    
    return result;
}

// Load configuration from JSON file
bool loadYoloConfig(const std::string& configFile, YoloConfig& config) {
    std::ifstream file(configFile);
    if (!file.is_open()) {
        printf("Warning: Could not open config file %s, using defaults\n", configFile.c_str());
        return false;
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string json = buffer.str();
    file.close();
    
    // Extract values
    float conf = extractFloatValue(json, "confidence_threshold");
    if (conf > 0.0f && conf <= 1.0f) {
        config.confidence_threshold = conf;
    }
    
    float nms = extractFloatValue(json, "nms_threshold");
    if (nms > 0.0f && nms <= 1.0f) {
        config.nms_threshold = nms;
    }
    
    config.roi_enabled = extractBoolValue(json, "roi_enabled");
    
    int roiX = (int)extractFloatValue(json, "roi_x");
    if (roiX >= 0) config.roi_x = roiX;
    
    int roiY = (int)extractFloatValue(json, "roi_y");
    if (roiY >= 0) config.roi_y = roiY;
    
    int roiW = (int)extractFloatValue(json, "roi_width");
    if (roiW > 0) config.roi_width = roiW;
    
    int roiH = (int)extractFloatValue(json, "roi_height");
    if (roiH > 0) config.roi_height = roiH;
    
    config.last_updated = extractStringValue(json, "last_updated");
    
    std::vector<int> classes = extractIntArray(json, "enabled_classes");
    if (!classes.empty()) {
        config.enabled_classes = classes;
    }
    
    printf("Loaded config: conf=%.2f, nms=%.2f, classes=%d, roi=%s\n",
           config.confidence_threshold, 
           config.nms_threshold,
           (int)config.enabled_classes.size(),
           config.roi_enabled ? "enabled" : "disabled");
    
    return true;
}

// Check if a class ID is enabled
bool isClassEnabled(const YoloConfig& config, int classId) {
    for (size_t i = 0; i < config.enabled_classes.size(); i++) {
        if (config.enabled_classes[i] == classId) {
            return true;
        }
    }
    return false;
}

#endif // __CONFIG_LOADER_H
