#ifndef IOTFLOW_CONFIG_H
#define IOTFLOW_CONFIG_H

// Server configuration
#ifndef IOTFLOW_SERVER_URL
#define IOTFLOW_SERVER_URL "http://192.168.0.13:5000"
#endif
#define DEVICE_REGISTRATION_ENDPOINT "/api/v1/devices/register"
#define API_KEY_REGISTRATION_ENDPOINT "/api/v1/devices/mqtt-credentials"

// MQTT configuration
#define MQTT_BROKER_URL "192.168.0.13"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "ESP32_Client"
#define MQTT_TOPIC "iotflow/device/data"

// Device configuration
#define DEVICE_ID "ESP32_100"
#define DEVICE_NAME "ESP32 IoTFlow Client 003"
#define DEVICE_TYPE "ESP32"

#endif // IOTFLOW_CONFIG_H