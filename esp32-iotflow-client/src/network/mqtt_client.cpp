#include "mqtt_client.h"
#include <WiFi.h>
#include <PubSubClient.h>

WiFiClient wifiClient;
PubSubClient client(wifiClient);

MQTTClient::MQTTClient(const char* broker, int port)
    : broker(broker), port(port) {
    client.setServer(broker, port);
}

void MQTTClient::connect(const char* clientId, const char* username, const char* password) {
    while (!client.connected()) {
        if (client.connect(clientId, username, password)) {
            // Successfully connected
        } else {
            delay(5000);
        }
    }
}

void MQTTClient::subscribe(const char* topic) {
    client.subscribe(topic);
}

void MQTTClient::publish(const char* topic, const char* payload) {
    client.publish(topic, payload);
}

void MQTTClient::loop() {
    client.loop();
}