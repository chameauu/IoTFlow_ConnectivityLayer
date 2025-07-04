#ifndef DEVICE_REGISTRATION_H
#define DEVICE_REGISTRATION_H

#include <Arduino.h>
#include "../utils/json_parser.h"
#include "api_key_manager.h"

class DeviceRegistration {
public:
    DeviceRegistration(const String& serverUrl, ApiKeyManager& apiKeyManager);
    bool registerDevice(const String& deviceId);
    bool isRegistered() const;
    bool hasStoredApiKey() const;
    bool verifyExistingRegistration();

private:
    String serverUrl;
    bool registered;
    ApiKeyManager& apiKeyManager;
};

#endif // DEVICE_REGISTRATION_H