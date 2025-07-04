#include "json_parser.h"
#include <ArduinoJson.h>

String parseJsonResponse(const String& jsonResponse) {
    JsonDocument doc;
    String result;

    DeserializationError error = deserializeJson(doc, jsonResponse);
    if (error) {
        return "Failed to parse JSON";
    }

    // Assuming the JSON response has a key "data" we want to extract
    if (doc["data"].isNull() == false) {
        result = doc["data"].as<String>();
    } else {
        result = "Key 'data' not found in JSON response";
    }

    return result;
}

bool JsonParser::parseApiKeyResponse(const String& jsonResponse, String& apiKey) {
    Serial.println("Parsing API key from JSON response...");
    
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, jsonResponse);
    if (error) {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
        return false;
    }
    
    // Print the parsed JSON for debugging
    Serial.print("Parsed JSON: ");
    serializeJson(doc, Serial);
    Serial.println();
    
    // Check for various possible field names for the API key
    if (!doc["api_key"].isNull()) {
        apiKey = doc["api_key"].as<String>();
        Serial.print("Found API key: ");
        Serial.println(apiKey);
        return true;
    } else if (!doc["apiKey"].isNull()) {
        apiKey = doc["apiKey"].as<String>();
        Serial.print("Found apiKey: ");
        Serial.println(apiKey);
        return true;
    } else if (!doc["key"].isNull()) {
        apiKey = doc["key"].as<String>();
        Serial.print("Found key: ");
        Serial.println(apiKey);
        return true;
    } else if (!doc["token"].isNull()) {
        apiKey = doc["token"].as<String>();
        Serial.print("Found token: ");
        Serial.println(apiKey);
        return true;
    } else if (!doc["device"].isNull() && !doc["device"]["api_key"].isNull()) {
        apiKey = doc["device"]["api_key"].as<String>();
        Serial.print("Found device.api_key: ");
        Serial.println(apiKey);
        return true;
    } else if (!doc["username"].isNull()) {
        apiKey = doc["username"].as<String>();
        Serial.print("Found username as API key: ");
        Serial.println(apiKey);
        return true;
    } else if (!doc["password"].isNull()) {
        apiKey = doc["password"].as<String>();
        Serial.print("Found password as API key: ");
        Serial.println(apiKey);
        return true;
    } else {
        Serial.println("API key not found in JSON response");
        // Try to find other keys that might be present
        String keys = "";
        for (JsonPair kv : doc.as<JsonObject>()) {
            if (keys.length() > 0) keys += ", ";
            keys += kv.key().c_str();
        }
        Serial.print("Available keys in response: ");
        Serial.println(keys);
        return false;
    }
}