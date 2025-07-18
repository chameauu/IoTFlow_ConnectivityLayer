/*
ESP32 MQTT Client for IoTFlow Platform
Device: esp32_010

This example shows how to connect an ESP32 to your IoTFlow MQTT broker
and send simulated telemetry data using the correct topic structure and authentication.
*/

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <Preferences.h>

// DHT sensor configuration
#define DHT_PIN 23      // DHT sensor connected to GPIO 4
#define DHT_TYPE DHT11 // DHT11 sensor type
DHT dht(DHT_PIN, DHT_TYPE);

// WiFi credentials
const char* ssid = "CelluleRech";
const char* password = "cellrech2023$";

// Server settings
const char* server_host = "10.200.240.60";  // Replace with your server IP
const int mqtt_port = 1883;
const int http_port = 5000;  // Flask server port

// Device configuration
String device_name = "esp32_001";  // Unique device name
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

// Preferences for persistent storage
Preferences preferences;

// LED pin for remote control
#define LED_PIN 2  // Built-in LED on GPIO 2

// Timing
unsigned long lastSensorRead = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastExtendedInfo = 0;
const unsigned long SENSOR_INTERVAL = 2000;   // 2 second for debugging
const unsigned long HEARTBEAT_INTERVAL = 60000;  // 1 minute
const unsigned long EXTENDED_INFO_INTERVAL = 300000;  // 5 minutes

// Function declarations
void setup_wifi();
void mqtt_callback(char* topic, byte* payload, unsigned int length);
void reconnect();
void send_telemetry_data();
void send_heartbeat();
void send_command_response(String command, String status);
void send_device_status();
String get_iso_timestamp();
bool register_device_with_server();
void send_extended_device_info();
void load_device_credentials();
void save_device_credentials();

void setup() {
  Serial.begin(115200);
  delay(1000);  // Give serial time to initialize
  
  Serial.println("\n=== ESP32 IoTFlow Client Starting ===");
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.println("LED pin initialized");
  
  // Initialize DHT sensor
  dht.begin();
  Serial.println("DHT sensor initialized");
  
  // Load stored device credentials
  load_device_credentials();
  
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
  
  // Send real device data every second
  if (now - lastSensorRead > SENSOR_INTERVAL) {
    send_telemetry_data();
    lastSensorRead = now;
  }
  
  // Send heartbeat every minute
  if (now - lastHeartbeat > HEARTBEAT_INTERVAL) {
    send_heartbeat();
    lastHeartbeat = now;
  }
  
  // Send extended device info every 5 minutes
  if (now - lastExtendedInfo > EXTENDED_INFO_INTERVAL) {
    send_extended_device_info();
    lastExtendedInfo = now;
  }
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("✅ WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("");
    Serial.println("❌ WiFi connection failed");
  }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("📨 Message arrived [");
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
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.print("❌ JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Handle commands
  if (doc.containsKey("command")) {
    String command = doc["command"];
    
    if (command == "led_on") {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("💡 LED turned ON");
      send_command_response("led_on", "success");
    }
    else if (command == "led_off") {
      digitalWrite(LED_PIN, LOW);
      Serial.println("💡 LED turned OFF");
      send_command_response("led_off", "success");
    }
    else if (command == "get_status") {
      Serial.println("📊 Status requested");
      send_device_status();
    }
    else {
      Serial.println("❓ Unknown command: " + command);
      send_command_response(command, "unknown_command");
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
    Serial.print("🔌 Attempting MQTT connection...");
    
    // Create client ID
    String clientId = "esp32_";
    clientId += String(device_id);
    
    // Attempt to connect with Last Will and Testament
    String lwt_topic = "iotflow/devices/" + String(device_id) + "/status/offline";
    
    if (client.connect(clientId.c_str(), NULL, NULL, lwt_topic.c_str(), 1, true, "offline")) {
      Serial.println(" ✅ connected");
      
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
      
      Serial.println("📡 Subscribed to: " + command_topic);
      
    } else {
      Serial.print(" ❌ failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void send_telemetry_data() {
  // Read DHT sensor data
  float temperature = dht.readTemperature();    // Temperature in Celsius
  float humidity = dht.readHumidity();          // Humidity in %
  
  // Check if DHT readings are valid
  bool dht_valid = !isnan(temperature) && !isnan(humidity);
  
  // Get additional device data
  float cpu_temp = temperatureRead();           // ESP32 internal temperature sensor
  uint32_t free_heap = ESP.getFreeHeap();
  int32_t wifi_rssi = WiFi.RSSI();
  uint32_t uptime_seconds = millis() / 1000;
  
  // Create telemetry payload with real sensor data
  DynamicJsonDocument doc(512);
  doc["api_key"] = device_api_key;
  doc["ts"] = get_iso_timestamp();
  
  // Environmental sensors (DHT11)
  if (dht_valid) {
    doc["temperature"] = round(temperature);  // DHT11 gives integer values
    doc["humidity"] = round(humidity);        // DHT11 gives integer values
    doc["heat_index"] = round(dht.computeHeatIndex(temperature, humidity, false));
  } else {
    doc["temperature"] = nullptr;  // Indicate sensor error
    doc["humidity"] = nullptr;
    doc["sensor_error"] = "DHT_READ_FAILED";
  }
  
  // System metrics
  doc["cpu_temp"] = round(cpu_temp * 10) / 10.0;         // CPU temperature in Celsius
  doc["free_heap"] = free_heap;                          // Free heap memory in bytes  
  doc["uptime"] = uptime_seconds;                        // Uptime in seconds
  doc["wifi_rssi"] = wifi_rssi;                          // WiFi signal strength in dBm
  doc["led_state"] = digitalRead(LED_PIN);               // LED state
  
  // Convert to string
  String payload;
  serializeJson(doc, payload);
  
  // Publish to telemetry topic
  String topic = "iotflow/devices/" + String(device_id) + "/telemetry/sensors";
  
  // Debug information
  Serial.println("📊 Preparing DHT11 telemetry...");
  Serial.println("Topic: " + topic);
  Serial.println("Payload size: " + String(payload.length()) + " bytes");
  Serial.println("MQTT connected: " + String(client.connected()));
  
  if (dht_valid) {
    Serial.print("🌡️ Temperature: "); Serial.print(temperature, 0); Serial.println("°C");
    Serial.print("💧 Humidity: "); Serial.print(humidity, 0); Serial.println("%");
    Serial.print("🔥 Heat Index: "); Serial.print(dht.computeHeatIndex(temperature, humidity, false), 0); Serial.println("°C");
  } else {
    Serial.println("❌ DHT11 sensor read failed!");
  }
  
  Serial.print("🖥️ CPU Temp: "); Serial.print(cpu_temp, 1); Serial.println("°C");
  Serial.print("🧠 Free Heap: "); Serial.print(free_heap); Serial.println(" bytes");
  Serial.print("📶 WiFi RSSI: "); Serial.print(wifi_rssi); Serial.println(" dBm");
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    // Toggle LED state to indicate telemetry was sent
    bool current_led_state = digitalRead(LED_PIN);
    digitalWrite(LED_PIN, !current_led_state);
    
    if (dht_valid) {
      Serial.println("✅ DHT11 telemetry sent - Temp: " + String(temperature, 0) + "°C, Humidity: " + String(humidity, 0) + "%, CPU: " + String(cpu_temp, 1) + "°C");
    } else {
      Serial.println("✅ System telemetry sent (DHT error) - CPU: " + String(cpu_temp, 1) + "°C, Heap: " + String(free_heap) + " bytes");
    }
    Serial.println("💡 LED toggled " + String(!current_led_state ? "ON" : "OFF") + " (telemetry sent)");
  } else {
    Serial.println("❌ Failed to send telemetry");
    Serial.println("MQTT State: " + String(client.state()));
    
    // Try to reconnect if disconnected
    if (!client.connected()) {
      Serial.println("🔄 MQTT disconnected, attempting reconnect...");
      reconnect();
    }
  }
}

void send_heartbeat() {
  DynamicJsonDocument doc(512);
  doc["api_key"] = device_api_key;
  doc["timestamp"] = get_iso_timestamp();
  doc["status"] = "alive";
  doc["uptime"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/status/heartbeat";
  
  // Debug heartbeat too
  Serial.println("💓 Preparing heartbeat...");
  Serial.println("Topic: " + topic);
  Serial.println("Payload size: " + String(payload.length()) + " bytes");
  Serial.println("Payload: " + payload);
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("✅ Heartbeat sent successfully");
  } else {
    Serial.println("❌ Failed to send heartbeat");
    Serial.println("MQTT State: " + String(client.state()));
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
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("📝 Command response sent: " + command + " -> " + status);
  } else {
    Serial.println("❌ Failed to send command response");
  }
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
  status["firmware_version"] = firmware_version;
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/telemetry/metrics";
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("📊 Device status sent");
  } else {
    Serial.println("❌ Failed to send device status");
  }
}

void send_extended_device_info() {
  // Send detailed device information (less frequently)
  DynamicJsonDocument doc(1024);
  doc["api_key"] = device_api_key;
  doc["timestamp"] = get_iso_timestamp();
  
  // Detailed device info
  doc["chip_id"] = String(ESP.getEfuseMac(), HEX);
  doc["chip_model"] = ESP.getChipModel();
  doc["chip_revision"] = ESP.getChipRevision();
  doc["flash_size"] = ESP.getFlashChipSize();
  doc["sketch_size"] = ESP.getSketchSize();
  doc["free_sketch"] = ESP.getFreeSketchSpace();
  doc["wifi_ssid"] = WiFi.SSID();
  doc["wifi_mac"] = WiFi.macAddress();
  doc["wifi_ip"] = WiFi.localIP().toString();
  doc["wifi_channel"] = WiFi.channel();
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "iotflow/devices/" + String(device_id) + "/telemetry/device_info";
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("📋 Extended device info sent");
  } else {
    Serial.println("❌ Failed to send extended device info");
  }
}

String get_iso_timestamp() {
  // Simple timestamp - in production, use NTP for accurate time
  unsigned long epoch = millis() / 1000;
  return String(epoch);
}

bool register_device_with_server() {
  // Check if already registered
  if (device_registered && device_id != -1 && device_api_key != "") {
    Serial.println("ℹ️ Device already registered, skipping registration");
    return true;
  }
  
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
  doc["description"] = "ESP32 IoT device with DHT11 temperature and humidity sensor";
  doc["username"]="admin"
  doc["password"]="admin123"
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
  Serial.println("Device: " + device_name);
  
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
        
        // Save credentials to persistent storage
        save_device_credentials();
        
        Serial.println("✅ Device registered successfully!");
        Serial.println("📋 Device ID: " + String(device_id));
        Serial.println("🔑 API Key: " + device_api_key.substring(0, 8) + "...");
        Serial.println("💾 Credentials saved to persistent storage");
      } else {
        Serial.println("❌ Invalid response format - missing id or api_key");
      }
    } else {
      Serial.println("❌ Failed to parse registration response");
      Serial.println("Parse error: " + String(error.c_str()));
    }
  } else if (httpCode == 409) {  // Conflict - device already exists
    Serial.println("⚠️ Device already registered, extracting existing info...");
    
    // Try to parse the response to get device info (some servers return device info even on 409)
    DynamicJsonDocument responseDoc(1024);
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error && responseDoc.containsKey("device")) {
      JsonObject deviceInfo = responseDoc["device"];
      
      if (deviceInfo.containsKey("id") && deviceInfo.containsKey("api_key")) {
        device_id = deviceInfo["id"];
        device_api_key = deviceInfo["api_key"].as<String>();
        device_registered = true;
        success = true;
        
        // Save credentials to persistent storage
        save_device_credentials();
        
        Serial.println("✅ Using existing device registration!");
        Serial.println("📋 Device ID: " + String(device_id));
        Serial.println("🔑 API Key: " + device_api_key.substring(0, 8) + "...");
        Serial.println("💾 Credentials saved to persistent storage");
      } else {
        Serial.println("❌ Server response missing device info");
        Serial.println("💡 Change device_name in code or delete device from server database");
      }
    } else {
      Serial.println("❌ Failed to parse 409 response");
      Serial.println("💡 Change device_name in code or delete device from server database");
    }
  } else {
    Serial.println("❌ Registration failed with HTTP code: " + String(httpCode));
    Serial.println("Response: " + response);
  }
  
  http.end();
  return success;
}

void load_device_credentials() {
  // Initialize preferences
  preferences.begin("iotflow", false);  // false = read/write mode
  
  // Try to load stored credentials
  if (preferences.isKey("device_id") && preferences.isKey("api_key")) {
    device_id = preferences.getInt("device_id", -1);
    device_api_key = preferences.getString("api_key", "");
    
    if (device_id != -1 && device_api_key.length() > 0) {
      device_registered = true;
      Serial.println("💾 Loaded stored device credentials:");
      Serial.println("📋 Device ID: " + String(device_id));
      Serial.println("🔑 API Key: " + device_api_key.substring(0, 8) + "...");
    } else {
      Serial.println("⚠️ Invalid stored credentials, will register new device");
      device_registered = false;
    }
  } else {
    Serial.println("📝 No stored credentials found, will register new device");
    device_registered = false;
  }
  
  preferences.end();
}

void save_device_credentials() {
  // Save credentials to persistent storage
  preferences.begin("iotflow", false);  // false = read/write mode
  
  preferences.putInt("device_id", device_id);
  preferences.putString("api_key", device_api_key);
  
  preferences.end();
  
  Serial.println("💾 Device credentials saved to persistent storage");
}
