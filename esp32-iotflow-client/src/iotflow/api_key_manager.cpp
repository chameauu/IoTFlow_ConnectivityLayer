#include "api_key_manager.h"
#include <Preferences.h>
#include <Arduino.h>

ApiKeyManager::ApiKeyManager() {
    // Try to initialize NVS with retries
    const int maxRetries = 3;
    int retry = 0;
    bool initialized = false;
    
    while (!initialized && retry < maxRetries) {
        initialized = preferences.begin("iotflow", false);
        if (!initialized) {
            Serial.printf("Failed to initialize NVS for API key storage (attempt %d/%d)\n", retry+1, maxRetries);
            delay(500); // Wait a bit before retrying
            retry++;
        }
    }
    
    if (initialized) {
        Serial.println("NVS initialized for API key storage");
    } else {
        Serial.println("CRITICAL: Could not initialize NVS after multiple attempts");
    }
}

void ApiKeyManager::registerApiKey(const String& apiKey) {
    if (preferences.putString("api_key", apiKey)) {
        Serial.println("API key saved successfully");
    } else {
        Serial.println("Failed to save API key");
    }
}

String ApiKeyManager::getApiKey() const {
    String apiKey = preferences.getString("api_key", "");
    if (apiKey.length() > 0) {
        Serial.println("Retrieved API key: " + apiKey);
    } else {
        Serial.println("No API key found in storage");
    }
    return apiKey;
}

ApiKeyManager::~ApiKeyManager() {
    preferences.end();
}