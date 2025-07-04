#include "device_registration.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "../utils/json_parser.h"
#include "api_key_manager.h"
#include "../config/iotflow_config.h"

DeviceRegistration::DeviceRegistration(const String& serverUrl, ApiKeyManager& apiKeyManager)
    : serverUrl(serverUrl), registered(false), apiKeyManager(apiKeyManager) {}

bool DeviceRegistration::registerDevice(const String& deviceId) {
    // Check if device is already registered (has a stored API key)
    if (hasStoredApiKey()) {
        Serial.println("Device already has an API key stored - skipping registration");
        registered = true;
        return true;
    }
    
    Serial.println("No existing API key found - proceeding with device registration");
    
    const int maxRetries = 3;
    int retryCount = 0;
    
    while (retryCount < maxRetries) {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("Device registration failed: WiFi not connected");
            return false;
        }
        
        if (retryCount > 0) {
            Serial.print("Retry attempt ");
            Serial.print(retryCount);
            Serial.println(" of 3...");
            delay(2000); // Wait 2 seconds before retry
        }

        HTTPClient http;
        String url = serverUrl + DEVICE_REGISTRATION_ENDPOINT;
        Serial.print("Sending registration request to URL: ");
        Serial.println(url);
        
        // Debug network status
        Serial.print("WiFi status: ");
        switch(WiFi.status()) {
            case WL_CONNECTED: Serial.println("Connected"); break;
            case WL_NO_SHIELD: Serial.println("No shield"); break;
            case WL_IDLE_STATUS: Serial.println("Idle"); break;
            case WL_NO_SSID_AVAIL: Serial.println("No SSID available"); break;
            case WL_SCAN_COMPLETED: Serial.println("Scan completed"); break;
            case WL_CONNECT_FAILED: Serial.println("Connection failed"); break;
            case WL_CONNECTION_LOST: Serial.println("Connection lost"); break;
            case WL_DISCONNECTED: Serial.println("Disconnected"); break;
            default: Serial.println("Unknown");
        }
        Serial.print("Local IP: ");
        Serial.println(WiFi.localIP());
        
        // Set longer timeout
        http.setConnectTimeout(15000); // 15 second timeout
        
        // Set additional options to help diagnose connection issues
        http.setReuse(false);
        http.setTimeout(30000); // 30 second read timeout
        
        bool beginSuccess = http.begin(url);
        if (!beginSuccess) {
            Serial.println("Failed to initialize HTTP connection");
            Serial.println("This could be due to DNS resolution failure or invalid URL");
            Serial.print("Server URL: ");
            Serial.println(url);
            
            // Attempt a simple ping if DNS name resolution failed
            IPAddress serverIP;
            String serverHost = serverUrl;
            if (serverUrl.startsWith("http://")) {
                serverHost = serverUrl.substring(7); // Remove http://
            }
            
            int colonPos = serverHost.indexOf(':');
            if (colonPos > 0) {
                serverHost = serverHost.substring(0, colonPos); // Remove port
            }
            
            Serial.print("Attempting to resolve host: ");
            Serial.println(serverHost);
            
            if (WiFi.hostByName(serverHost.c_str(), serverIP)) {
                Serial.print("Resolved to IP: ");
                Serial.println(serverIP.toString());
            } else {
                Serial.println("Could not resolve hostname");
            }
            
            retryCount++;
            delay(2000); // Wait before retry
            continue;
        }
        
        http.addHeader("Content-Type", "application/json");

        String payload = "{\"device_id\":\"" + deviceId + "\", \"name\":\"" + String(DEVICE_NAME) + "\", \"device_type\":\"" + String(DEVICE_TYPE) + "\"}";
        Serial.print("Request payload: ");
        Serial.println(payload);
        
        int httpResponseCode = http.POST(payload);
        String response = http.getString();
        
        Serial.print("HTTP response code: ");
        Serial.println(httpResponseCode);
        Serial.print("Response: ");
        Serial.println(response);

    if (httpResponseCode == 200 || httpResponseCode == 201) {
        Serial.println("Registration HTTP request successful");
        String apiKey;
        if (JsonParser::parseApiKeyResponse(response, apiKey)) {
            Serial.println("API key parsed from response");
            apiKeyManager.registerApiKey(apiKey);
            registered = true;
            Serial.println("Device registered successfully");
            http.end();
            return true;
        } else {
            Serial.println("Failed to parse API key from response");
            Serial.println("Raw response was:");
            Serial.println(response);
            if (response.length() == 0) {
                Serial.println("Response was empty, which may indicate a server issue");
            }
        }
    } else if (httpResponseCode == 409) {
        Serial.println("Device already registered (HTTP 409 Conflict)");
        Serial.println("Try using a different device ID or check server logs");
        Serial.println(response);
    } else if (httpResponseCode < 0) {
        // Connection error
        Serial.print("Connection error: ");
        switch(httpResponseCode) {
            case -1: Serial.println("Connection refused or timeout"); break;
            case -2: Serial.println("Send header failed"); break;
            case -3: Serial.println("Send payload failed"); break;
            case -4: Serial.println("Not connected"); break;
            case -5: Serial.println("Connection lost"); break;
            case -6: Serial.println("No stream"); break;
            case -7: Serial.println("No HTTP server"); break;
            case -8: Serial.println("Too less RAM"); break;
            case -9: Serial.println("Encoding error"); break;
            case -10: Serial.println("Stream write error"); break;
            case -11: Serial.println("Read timeout"); break;
            default: Serial.println("Unknown error");
        }
        
        // Add troubleshooting suggestions
        Serial.println("\nTroubleshooting suggestions:");
        Serial.println("1. Check that the server is running and accessible");
        Serial.println("2. Verify the server URL and port are correct");
        Serial.println("3. Ensure the device has proper network connectivity");
        Serial.println("4. Check for firewall blocking the connection");
        
        // Try a raw TCP connection to test if the server port is reachable
        String serverHost = serverUrl;
        int serverPort = 5000; // Default port
        
        // Extract host and port from URL
        if (serverUrl.startsWith("http://")) {
            serverHost = serverUrl.substring(7); // Remove http://
        }
        
        int colonPos = serverHost.indexOf(':');
        if (colonPos > 0) {
            serverPort = serverHost.substring(colonPos + 1).toInt();
            serverHost = serverHost.substring(0, colonPos);
        }
        
        // Extract path part if present
        int slashPos = serverHost.indexOf('/');
        if (slashPos > 0) {
            serverHost = serverHost.substring(0, slashPos);
        }
        
        Serial.print("Testing direct TCP connection to ");
        Serial.print(serverHost);
        Serial.print(":");
        Serial.println(serverPort);
        
        WiFiClient client;
        if (client.connect(serverHost.c_str(), serverPort)) {
            Serial.println("TCP connection successful but HTTP request failed.");
            Serial.println("This suggests the server is reachable but may not be handling HTTP correctly.");
            client.stop();
        } else {
            Serial.println("TCP connection failed. The server port appears to be closed or blocked.");
        }
    } else {
        Serial.print("HTTP request failed with code: ");
        Serial.println(httpResponseCode);
        Serial.print("Response: ");
        Serial.println(response);
    }

        http.end();
        retryCount++;
    }
    
    Serial.println("Device registration failed after all retry attempts");
    return false;
}

bool DeviceRegistration::isRegistered() const {
    return registered;
}

bool DeviceRegistration::hasStoredApiKey() const {
    String apiKey = apiKeyManager.getApiKey();
    return apiKey.length() > 0;
}

bool DeviceRegistration::verifyExistingRegistration() {
    if (hasStoredApiKey()) {
        Serial.println("API key found in storage - device appears to be already registered");
        registered = true;
        return true;
    }
    return false;
}