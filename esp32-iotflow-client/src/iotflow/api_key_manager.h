#ifndef API_KEY_MANAGER_H
#define API_KEY_MANAGER_H

#include <Arduino.h>
#include <Preferences.h>

class ApiKeyManager {
public:
    ApiKeyManager();
    void registerApiKey(const String& apiKey);
    String getApiKey() const;
    ~ApiKeyManager();

private:
    mutable Preferences preferences;
};

#endif // API_KEY_MANAGER_H