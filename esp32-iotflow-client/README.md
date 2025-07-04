# ESP32 IoTFlow Client

This project is designed for the ESP32 microcontroller to connect and interact with the IoTFlow server. It includes functionalities for device registration, API key management, and MQTT communication.

## Project Structure

```
esp32-iotflow-client
├── src
│   ├── main.cpp                # Entry point of the application
│   ├── config
│   │   ├── wifi_config.h       # Wi-Fi configuration settings
│   │   └── iotflow_config.h    # IoTFlow server configuration settings
│   ├── network
│   │   ├── wifi_manager.cpp     # Implementation of WiFiManager
│   │   ├── wifi_manager.h       # Declaration of WiFiManager
│   │   ├── mqtt_client.cpp      # Implementation of MQTTClient
│   │   └── mqtt_client.h        # Declaration of MQTTClient
│   ├── iotflow
│   │   ├── device_registration.cpp # Implementation of DeviceRegistration
│   │   ├── device_registration.h   # Declaration of DeviceRegistration
│   │   ├── api_key_manager.cpp     # Implementation of ApiKeyManager
│   │   └── api_key_manager.h       # Declaration of ApiKeyManager
│   └── utils
│       ├── json_parser.cpp         # JSON parsing utility functions
│       └── json_parser.h           # Declaration of JSON parsing functions
├── lib                            # External libraries
├── include                         # Additional shared header files
├── platformio.ini                 # PlatformIO configuration file
└── README.md                      # Project documentation
```

## Setup Instructions

1. **Clone the Repository**
   Clone this repository to your local machine using:
   ```
   git clone <repository-url>
   ```

2. **Install PlatformIO**
   Ensure you have PlatformIO installed. You can install it as a plugin in Visual Studio Code or use the command line.

3. **Configure Wi-Fi and IoTFlow Settings**
   Update the `wifi_config.h` and `iotflow_config.h` files in the `src/config` directory with your Wi-Fi credentials and IoTFlow server details.

4. **Build the Project**
   Navigate to the project directory and build the project using PlatformIO:
   ```
   pio run
   ```

5. **Upload to ESP32**
   Connect your ESP32 board and upload the firmware:
   ```
   pio run --target upload
   ```

## Usage

Once uploaded, the ESP32 will connect to the specified Wi-Fi network, register with the IoTFlow server, and subscribe to the MQTT broker using the provided API key. You can monitor the device's activity through the serial console.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.