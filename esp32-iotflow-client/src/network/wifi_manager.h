class WiFiManager {
public:
    WiFiManager();
    void connectToWiFi(const char* ssid, const char* password);
    bool isConnected();
    void disconnect();

private:
    void handleWiFiEvent();
};