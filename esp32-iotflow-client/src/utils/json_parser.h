#ifndef JSON_PARSER_H
#define JSON_PARSER_H

#include <ArduinoJson.h>

class JsonParser {
public:
    static bool parseDeviceRegistrationResponse(const String& jsonResponse, String& deviceId);
    static bool parseApiKeyResponse(const String& jsonResponse, String& apiKey);
};

#endif // JSON_PARSER_H