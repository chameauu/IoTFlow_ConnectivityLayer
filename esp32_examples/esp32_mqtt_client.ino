/*
ESP32 MQTT Client for IoTFlow Platform
Device: my_esp32_001

This example shows how to connect an ESP32 to your IoTFlow MQTT broker
and send telemetry data using the correct topic structure and authentication.
*/

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <DHT.h>

// Ensure Serial is available
#ifndef Serial
#define Serial Serial
#endif

// WiFi credentials
const char* ssid = "LPS";
const char* password = "UR11ES76";

// Server settings
const char* server_host = "10.200.230.246";  // Replace with your server IP
const int mqtt_port = 1883;
const int http_port = 5000;  // Flask server port

// Device configuration
String device_name = "esp32_010";  // Unique device name
String device_type = "esp32";
String firmware_version = "1.0.0";
String location = "lab";

// Runtime variables (will be set after registration)
int device_id = -1;  // Will be assigned by server
String device_api_key = "";  // Will be received from server
bool device_registered = false;

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// DHT sensor (optional - for real sensor data)
#define DHT_PIN 4  // Changed to GPIO 4 to avoid conflict
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// LED pin for remote control
#define LED_PIN 2  // Use GPIO 2 for LED

// Timing
unsigned long lastSensorRead = 0;
unsigned long lastHeartbeat = 0;
const unsigned long SENSOR_INTERVAL = 30000;  // 30 seconds
const unsigned long HEARTBEAT_INTERVAL = 60000;  // 1 minute

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize DHT sensor
  dht.begin();
  
  // Connect to WiFi
  setup_wifi();
  
  // Register device with server before MQTT
  if (register_device_with_server()) {
    Serial.println("✅ Device registered successfully");
    
    // Setup MQTT only after successful registration
    client.setServer(server_host, mqtt_port);
    client.setCallback(mqtt_callback);
    
    Serial.println("ESP32 ready for IoTFlow connection");
  } else {
    Serial.println("❌ Device registration failed - will retry");
  }
}

void loop() {
  // Only proceed if device is registered
  if (!device_registered) {
    // Try to register every 30 seconds
    static unsigned long last_registration_attempt = 0;
    if (millis() - last_registration_attempt > 30000) {
      Serial.println("🔄 Attempting device registration...");
      if (register_device_with_server()) {
        Serial.println("✅ Device registered successfully");
        client.setServer(server_host, mqtt_port);
        client.setCallback(mqtt_callback);
      }
      last_registration_attempt = millis();
    }
    delay(1000);
    return;
  }
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  unsigned long now = millis();
  
  // Send sensor data every 30 seconds
  if (now - lastSensorRead > SENSOR_INTERVAL) {
    send_telemetry_data();
    lastSensorRead = now;
  }
  
  // Send heartbeat every minute
  if (now - lastHeartbeat > HEARTBEAT_INTERVAL) {
    send_heartbeat();
    lastHeartbeat = now;
  }
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  // Convert payload to string
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Parse JSON command
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, message);
  
  // Handle commands
  if (doc.containsKey("command")) {
    String command = doc["command"];
    
    if (command == "led_on") {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED turned ON");
      send_command_response("led_on", "success");
    }
    else if (command == "led_off") {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED turned OFF");
      send_command_response("led_off", "success");
    }
    else if (command == "get_status") {
      send_device_status();
    }
  }
}

void reconnect() {
  // Don't attempt MQTT connection if device is not registered
  if (!device_registered || device_id == -1 || device_api_key == "") {
    Serial.println("⚠️ Device not registered, cannot connect to MQTT");
    return;
  }
  
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Create client ID
    String clientId = "esp32_";
    clientId += String(device_id);
    
    // Attempt to connect with Last Will and Testament
    String lwt_topic = "iotflow/devices/" + String(device_id) + "/status/offline";
    
    if (client.connect(clientId.c_str(), NULL, NULL, lwt_topic.c_str(), 1, true, "offline")) {
      Serial.println("connected");
      
      // Send online status with API key for authentication
      String online_topic = "iotflow/devices/" + String(device_id) + "/status/online";
      
      // Create authenticated online message
      DynamicJsonDocument onlineDoc(512);
      onlineDoc["api_key"] = device_api_key;
      onlineDoc["timestamp"] = get_iso_timestamp();
      onlineDoc["status"] = "online";
      onlineDoc["device_id"] = device_id;
      
      String onlinePayload;
      serializeJson(onlineDoc, onlinePayload);
      
      client.publish(online_topic.c_str(), onlinePayload.c_str(), true);
      
      // Subscribe to commands
      String command_topic = "iotflow/devices/" + String(device_id) + "/commands/control";
      client.subscribe(command_topic.c_str());
      
      Serial.println("Subscribed to: " + command_topic);
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void send_telemetry_data() {
  // Read sensor data (or simulate if no sensors)
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // If DHT reading failed, use simulated data
  if (isnan(temperature) || isnan(humidity)) {
    temperature = 20.0 + random(-5, 10);  // Random temp between 15-30°C
    humidity = 50.0 + random(-10, 20);    // Random humidity between 40-70%
  }
  
  // Create telemetry payload according to your system's format
  DynamicJsonDocument doc(1024);
  doc["api_key"] = device_api_key;
  doc["timestamp"] = get_iso_timestamp();
  
  // Sensor data
  JsonObject data = doc.createNestedObject("data");
  data["temperature"] = temperature;
  data["humidity"] = humidity;
  data["wifi_rssi"] = WiFi.RSSI();
  data["free_heap"] = ESP.getFreeHeap();
  data["uptime"] = millis() / 1000;
  
  // Metadata
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["device_type"] = "esp32";
  metadata["firmware_version"] = "1.0.0";
  metadata["location"] = "lab";
  
  // Convert to string
  String payload;
  serializeJson(doc, payload);
  
  // Publish to telemetry topic
  String topic = "iotflow/devices/" + String(device_id) + "/telemetry/sensors";
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("Telemetry sent: " + payload);
  } else {
    Serial.println("Failed to send telemetry");
  }
}

void send_heartbeat() {
  DynamicJsonDocument doc(512);
  doc["api_key"] = device_api_key;
  doc["timestamp"] = get_iso_timestamp();
  doc["status"] = "alive";
  doc["uptime"] = millis() / 1000;
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/status/heartbeat";
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("Heartbeat sent");
  }
}

void send_command_response(String command, String status) {
  DynamicJsonDocument doc(512);
  doc["api_key"] = device_api_key;
  doc["timestamp"] = get_iso_timestamp();
  doc["command"] = command;
  doc["status"] = status;
  doc["device_id"] = device_id;
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/telemetry/events";
  client.publish(topic.c_str(), payload.c_str());
}

void send_device_status() {
  DynamicJsonDocument doc(1024);
  doc["api_key"] = device_api_key;
  doc["timestamp"] = get_iso_timestamp();
  
  JsonObject status = doc.createNestedObject("data");
  status["device_id"] = device_id;
  status["wifi_connected"] = WiFi.isConnected();
  status["wifi_ssid"] = WiFi.SSID();
  status["wifi_rssi"] = WiFi.RSSI();
  status["ip_address"] = WiFi.localIP().toString();
  status["free_heap"] = ESP.getFreeHeap();
  status["uptime"] = millis() / 1000;
  status["led_state"] = digitalRead(LED_PIN) ? "on" : "off";
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/telemetry/metrics";
  client.publish(topic.c_str(), payload.c_str());
}

String get_iso_timestamp() {
  // Simple timestamp - in production, use NTP for accurate time
  unsigned long epoch = millis() / 1000;
  return String(epoch);
}

bool register_device_with_server() {
  /*
   * Register the ESP32 device with the IoTFlow server via HTTP API
   * Returns true if successful, false otherwise
   */
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected, cannot register");
    return false;
  }
  
  HTTPClient http;
  String url = "http://" + String(server_host) + ":" + String(http_port) + "/api/v1/devices/register";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Create registration payload
  DynamicJsonDocument doc(1024);
  doc["name"] = device_name;
  doc["device_type"] = device_type;
  doc["description"] = "ESP32 IoT device with temperature and humidity sensors";
  doc["location"] = location;
  doc["firmware_version"] = firmware_version;
  doc["hardware_version"] = "ESP32-WROOM-32";
  
  // Add device capabilities
  JsonArray capabilities = doc.createNestedArray("capabilities");
  capabilities.add("temperature");
  capabilities.add("humidity");
  capabilities.add("wifi_monitoring");
  capabilities.add("remote_control");
  
  // Add device metadata
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["mac_address"] = WiFi.macAddress();
  metadata["chip_model"] = ESP.getChipModel();
  metadata["chip_revision"] = ESP.getChipRevision();
  metadata["cpu_freq_mhz"] = ESP.getCpuFreqMHz();
  metadata["flash_size"] = ESP.getFlashChipSize();
  
  String payload;
  serializeJson(doc, payload);
  
  Serial.println("📡 Registering device with server...");
  Serial.println("URL: " + url);
  Serial.println("Payload: " + payload);
  
  int httpCode = http.POST(payload);
  String response = http.getString();
  
  Serial.println("📡 HTTP Response Code: " + String(httpCode));
  Serial.println("📡 HTTP Response: " + response);
  
  bool success = false;
  
  if (httpCode == 201) {  // Created
    // Parse response to get device ID and API key
    DynamicJsonDocument responseDoc(1024);
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error && responseDoc.containsKey("device")) {
      JsonObject deviceInfo = responseDoc["device"];
      
      if (deviceInfo.containsKey("id") && deviceInfo.containsKey("api_key")) {
        device_id = deviceInfo["id"];
        device_api_key = deviceInfo["api_key"].as<String>();
        device_registered = true;
        success = true;
        
        Serial.println("✅ Device registered successfully!");
        Serial.println("📋 Device ID: " + String(device_id));
        Serial.println("🔑 API Key: " + device_api_key.substring(0, 8) + "...");
      } else {
        Serial.println("❌ Invalid response format - missing id or api_key");
      }
    } else {
      Serial.println("❌ Failed to parse registration response");
    }
  } else if (httpCode == 409) {  // Conflict - device already exists
    Serial.println("⚠️ Device already registered, trying to get existing info...");
    
    // Try to get device info by querying the server
    if (get_existing_device_info()) {
      success = true;
    }
  } else {
    Serial.println("❌ Registration failed with HTTP code: " + String(httpCode));
    Serial.println("Response: " + response);
  }
  
  http.end();
  return success;
}

bool get_existing_device_info() {
  /*
   * Get device info for already registered device
   * This would require implementing a device lookup endpoint
   * For now, return false to force re-registration with different name
   */
  Serial.println("💡 If device exists, change device_name in code or delete from server database");
  return false;
}
