#include <Arduino.h>
#include <WiFi.h>
#include <nvs_flash.h>  // Include the NVS flash header
#include <ESP32Ping.h> // Include ESP32 Ping library
#include "config/wifi_config.h"
#include "config/iotflow_config.h"
#include "iotflow/device_registration.h"
#include "iotflow/api_key_manager.h"
#include "network/mqtt_client.h"
#include "network/wifi_manager.h"

WiFiManager wifiManager;
ApiKeyManager apiKeyManager;
DeviceRegistration deviceRegistration(IOTFLOW_SERVER_URL, apiKeyManager);
MQTTClient* mqttClient = nullptr;

void setup() {
    // Initialize serial and wait a moment to ensure it's ready
    Serial.begin(115200);
    delay(1000); // Give time for serial to initialize
    
    Serial.println("\n\n--- ESP32 IoTFlow Client Starting ---");
    
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        Serial.println("Erasing NVS flash...");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    Serial.println("NVS Flash initialized successfully");
    
    Serial.println("Connecting to WiFi SSID: " + String(WIFI_SSID));
    
    wifiManager.connectToWiFi(WIFI_SSID, WIFI_PASSWORD);
    
    if (wifiManager.isConnected()) {
        Serial.println("WiFi connected successfully");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
        
        // Test server reachability
        IPAddress serverIP;
        String serverHost = String(IOTFLOW_SERVER_URL).substring(7);  // Remove http://
        int colonPos = serverHost.indexOf(':');
        int serverPort = 5000; // Default port
        
        if (colonPos > 0) {
            serverPort = serverHost.substring(colonPos + 1).toInt();
            serverHost = serverHost.substring(0, colonPos);  // Remove port if present
        }
        
        Serial.print("Testing connection to server host: ");
        Serial.println(serverHost);
        
        if(WiFi.hostByName(serverHost.c_str(), serverIP)) {
            Serial.print("Server IP: ");
            Serial.println(serverIP.toString());
            Serial.print("Server Port: ");
            Serial.println(serverPort);
            
            Serial.println("Pinging server...");
            if(Ping.ping(serverIP)) {
                Serial.println("Server ping successful");
            } else {
                Serial.println("Server ping failed - continuing anyway");
            }
            
            // Try a TCP connection to test if the HTTP service is running
            WiFiClient client;
            Serial.println("Testing TCP connection to server port...");
            if (client.connect(serverIP, serverPort)) {
                Serial.println("TCP connection successful - HTTP service appears to be running");
                client.stop();
            } else {
                Serial.println("WARNING: Could not connect to server on port " + String(serverPort));
                Serial.println("This may indicate the HTTP service is not running or is blocked");
            }
        } else {
            Serial.println("Could not resolve server hostname - continuing anyway");
        }
        
        // Check if device is already registered
        if (deviceRegistration.verifyExistingRegistration()) {
            Serial.println("Device is already registered with a stored API key");
        } else {
            Serial.println("Registering device with server: " + String(IOTFLOW_SERVER_URL));
            Serial.println("Device ID: " + String(DEVICE_ID));
            
            if (!deviceRegistration.registerDevice(DEVICE_ID)) {
                Serial.println("Device registration failed, cannot proceed");
                return; // Stop setup if registration fails
            }
        }
        
        // Whether newly registered or using existing registration, get the API key
        String apiKey = apiKeyManager.getApiKey();
        if (apiKey.length() > 0) {
            Serial.println("API key available.");
            
            Serial.print("Connecting to MQTT broker: ");
            Serial.println(String(MQTT_BROKER_URL) + ":" + String(MQTT_PORT));
            
            mqttClient = new MQTTClient(MQTT_BROKER_URL, MQTT_PORT);
            mqttClient->connect(MQTT_CLIENT_ID, apiKey.c_str(), nullptr);
            
            Serial.println("Connected to MQTT broker.");
            Serial.print("Subscribing to topic: ");
            Serial.println(MQTT_TOPIC);
            
            mqttClient->subscribe(MQTT_TOPIC);
        } else {
            Serial.println("Failed to obtain API key.");
        }
    } else {
        Serial.println("WiFi connection failed.");
    }
}

void loop() {
    if (mqttClient) {
        mqttClient->loop();
    }
    
    // Add a short delay to prevent watchdog timer issues
    delay(100);
}