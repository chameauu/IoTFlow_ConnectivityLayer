"""
MQTT Client Service for IoTFlow
Handles MQTT connections, authentication, and message processing
"""

import json
import logging
import ssl
import threading
import time
from typing import Dict, Callable, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet

from .topics import MQTTTopicManager, QoSLevel, TopicType


@dataclass
class MQTTConfig:
    """MQTT broker configuration"""
    host: str = "localhost"
    port: int = 1883
    keepalive: int = 60
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    clean_session: bool = True
    
    # TLS/SSL configuration
    use_tls: bool = False
    tls_port: int = 8883
    ca_cert_path: Optional[str] = None
    cert_file_path: Optional[str] = None
    key_file_path: Optional[str] = None
    tls_insecure: bool = False
    
    # Connection settings
    max_retries: int = 5
    retry_delay: int = 5
    auto_reconnect: bool = True
    
    # Message settings
    max_inflight_messages: int = 20
    message_retry_set: int = 20
    
    # Quality of Service
    default_qos: int = 1


@dataclass
class MQTTMessage:
    """Represents an MQTT message"""
    topic: str
    payload: Any
    qos: int = 1
    retain: bool = False
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert message to dictionary"""
        return {
            "topic": self.topic,
            "payload": self.payload,
            "qos": self.qos,
            "retain": self.retain,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class MQTTMessageHandler:
    """Base class for handling MQTT messages"""
    
    def __init__(self, topic_pattern: str):
        self.topic_pattern = topic_pattern
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def can_handle(self, topic: str) -> bool:
        """Check if this handler can process the given topic"""
        # Simple wildcard matching
        pattern_parts = self.topic_pattern.split("/")
        topic_parts = topic.split("/")
        
        if len(pattern_parts) != len(topic_parts):
            return False
        
        for pattern_part, topic_part in zip(pattern_parts, topic_parts):
            if pattern_part == "+":
                continue
            elif pattern_part == "#":
                return True
            elif pattern_part != topic_part:
                return False
        
        return True
    
    def handle_message(self, message: MQTTMessage) -> None:
        """Handle the MQTT message"""
        raise NotImplementedError("Subclasses must implement handle_message")


class TelemetryMessageHandler(MQTTMessageHandler):
    """Handles device telemetry messages"""
    
    def __init__(self):
        super().__init__("iotflow/devices/+/telemetry/+")
        self.telemetry_callbacks: List[Callable] = []
    
    def add_telemetry_callback(self, callback: Callable):
        """Add a callback for telemetry data"""
        self.telemetry_callbacks.append(callback)
    
    def handle_message(self, message: MQTTMessage) -> None:
        """Process telemetry message"""
        try:
            # Parse topic to extract device info
            parsed_topic = MQTTTopicManager.parse_topic(message.topic)
            if not parsed_topic:
                self.logger.warning(f"Invalid telemetry topic: {message.topic}")
                return
            
            device_id = parsed_topic.get("device_id")
            subtopic = parsed_topic.get("subtopic")
            
            # Parse payload
            if isinstance(message.payload, (str, bytes)):
                try:
                    payload_data = json.loads(message.payload)
                except json.JSONDecodeError:
                    payload_data = {"raw_data": message.payload}
            else:
                payload_data = message.payload
            
            # Enrich with metadata
            telemetry_data = {
                "device_id": device_id,
                "telemetry_type": subtopic,
                "data": payload_data,
                "timestamp": message.timestamp,
                "topic": message.topic,
                "qos": message.qos
            }
            
            # Call registered callbacks
            for callback in self.telemetry_callbacks:
                try:
                    callback(telemetry_data)
                except Exception as e:
                    self.logger.error(f"Error in telemetry callback: {e}")
            
            self.logger.debug(f"Processed telemetry from device {device_id}: {subtopic}")
            
        except Exception as e:
            self.logger.error(f"Error processing telemetry message: {e}")


class CommandMessageHandler(MQTTMessageHandler):
    """Handles device command messages"""
    
    def __init__(self):
        super().__init__("iotflow/devices/+/commands/+")
        self.command_callbacks: List[Callable] = []
    
    def add_command_callback(self, callback: Callable):
        """Add a callback for command processing"""
        self.command_callbacks.append(callback)
    
    def handle_message(self, message: MQTTMessage) -> None:
        """Process command message"""
        try:
            parsed_topic = MQTTTopicManager.parse_topic(message.topic)
            if not parsed_topic:
                self.logger.warning(f"Invalid command topic: {message.topic}")
                return
            
            device_id = parsed_topic.get("device_id")
            command_type = parsed_topic.get("subtopic")
            
            # Parse command payload
            if isinstance(message.payload, (str, bytes)):
                try:
                    command_data = json.loads(message.payload)
                except json.JSONDecodeError:
                    command_data = {"raw_command": message.payload}
            else:
                command_data = message.payload
            
            # Enrich with metadata
            command_info = {
                "device_id": device_id,
                "command_type": command_type,
                "command": command_data,
                "timestamp": message.timestamp,
                "topic": message.topic
            }
            
            # Call registered callbacks
            for callback in self.command_callbacks:
                try:
                    callback(command_info)
                except Exception as e:
                    self.logger.error(f"Error in command callback: {e}")
            
            self.logger.info(f"Processed command for device {device_id}: {command_type}")
            
        except Exception as e:
            self.logger.error(f"Error processing command message: {e}")


class StatusMessageHandler(MQTTMessageHandler):
    """Handles device status messages"""
    
    def __init__(self):
        super().__init__("iotflow/devices/+/status/+")
        self.status_callbacks: List[Callable] = []
    
    def add_status_callback(self, callback: Callable):
        """Add a callback for status updates"""
        self.status_callbacks.append(callback)
    
    def handle_message(self, message: MQTTMessage) -> None:
        """Process status message"""
        try:
            parsed_topic = MQTTTopicManager.parse_topic(message.topic)
            if not parsed_topic:
                self.logger.warning(f"Invalid status topic: {message.topic}")
                return
            
            device_id = parsed_topic.get("device_id")
            status_type = parsed_topic.get("subtopic")
            
            # Parse status payload
            if isinstance(message.payload, (str, bytes)):
                try:
                    status_data = json.loads(message.payload)
                except json.JSONDecodeError:
                    status_data = {"raw_status": message.payload}
            else:
                status_data = message.payload
            
            # Enrich with metadata
            status_info = {
                "device_id": device_id,
                "status_type": status_type,
                "status": status_data,
                "timestamp": message.timestamp,
                "topic": message.topic
            }
            
            # Call registered callbacks
            for callback in self.status_callbacks:
                try:
                    callback(status_info)
                except Exception as e:
                    self.logger.error(f"Error in status callback: {e}")
            
            self.logger.debug(f"Processed status from device {device_id}: {status_type}")
            
        except Exception as e:
            self.logger.error(f"Error processing status message: {e}")


class MQTTClientService:
    """
    Main MQTT client service for IoTFlow
    Handles connections, subscriptions, and message routing
    """
    
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.message_handlers: List[MQTTMessageHandler] = []
        self.subscription_callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Initialize default message handlers
        self.telemetry_handler = TelemetryMessageHandler()
        self.command_handler = CommandMessageHandler()
        self.status_handler = StatusMessageHandler()
        
        self.add_message_handler(self.telemetry_handler)
        self.add_message_handler(self.command_handler)
        self.add_message_handler(self.status_handler)
    
    def add_message_handler(self, handler: MQTTMessageHandler):
        """Add a message handler"""
        self.message_handlers.append(handler)
    
    def add_telemetry_callback(self, callback: Callable):
        """Add callback for telemetry data"""
        self.telemetry_handler.add_telemetry_callback(callback)
    
    def add_command_callback(self, callback: Callable):
        """Add callback for command processing"""
        self.command_handler.add_command_callback(callback)
    
    def add_status_callback(self, callback: Callable):
        """Add callback for status updates"""
        self.status_handler.add_status_callback(callback)
    
    def _setup_client(self):
        """Setup MQTT client with configuration"""
        client_id = self.config.client_id or f"iotflow_server_{int(time.time())}"
        self.client = mqtt.Client(client_id=client_id, clean_session=self.config.clean_session)
        
        # Set credentials if provided
        if self.config.username and self.config.password:
            self.client.username_pw_set(self.config.username, self.config.password)
        
        # Configure TLS if enabled
        if self.config.use_tls:
            self._setup_tls()
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_log = self._on_log
        
        # Configure client options
        self.client.max_inflight_messages_set(self.config.max_inflight_messages)
        self.client.message_retry_set(self.config.message_retry_set)
    
    def _setup_tls(self):
        """Setup TLS/SSL configuration"""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        if self.config.ca_cert_path:
            context.load_verify_locations(self.config.ca_cert_path)
        
        if self.config.cert_file_path and self.config.key_file_path:
            context.load_cert_chain(self.config.cert_file_path, self.config.key_file_path)
        
        if self.config.tls_insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        self.client.tls_set_context(context)
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            if not self.client:
                self._setup_client()
            
            port = self.config.tls_port if self.config.use_tls else self.config.port
            
            self.logger.info(f"Connecting to MQTT broker at {self.config.host}:{port}")
            result = self.client.connect(self.config.host, port, self.config.keepalive)
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                # Start the network loop
                self.client.loop_start()
                return True
            else:
                self.logger.error(f"Failed to connect to MQTT broker: {mqtt.error_string(result)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            if self.client and self.connected:
                self.logger.info("Disconnecting from MQTT broker")
                self.client.loop_stop()
                self.client.disconnect()
                self.connected = False
        except Exception as e:
            self.logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    def publish(self, topic: str, payload: Any, qos: int = None, retain: bool = False) -> bool:
        """
        Publish a message to MQTT broker
        
        Args:
            topic: Topic to publish to
            payload: Message payload
            qos: Quality of service level
            retain: Whether to retain the message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            self.logger.warning("Cannot publish: not connected to MQTT broker")
            return False
        
        try:
            # Use default QoS if not specified
            qos = qos if qos is not None else self.config.default_qos
            
            # Convert payload to JSON if it's a dict/list
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload)
            
            # Publish message
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                self.logger.error(f"Failed to publish to {topic}: {mqtt.error_string(result.rc)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing message: {e}")
            return False
    
    def subscribe(self, topic: str, qos: int = None, callback: Callable = None) -> bool:
        """
        Subscribe to a topic
        
        Args:
            topic: Topic to subscribe to
            qos: Quality of service level
            callback: Optional callback for this specific topic
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            self.logger.warning("Cannot subscribe: not connected to MQTT broker")
            return False
        
        try:
            qos = qos if qos is not None else self.config.default_qos
            
            result = self.client.subscribe(topic, qos=qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Subscribed to {topic} with QoS {qos}")
                
                # Register callback if provided
                if callback:
                    if topic not in self.subscription_callbacks:
                        self.subscription_callbacks[topic] = []
                    self.subscription_callbacks[topic].append(callback)
                
                return True
            else:
                self.logger.error(f"Failed to subscribe to {topic}: {mqtt.error_string(result[0])}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error subscribing to topic: {e}")
            return False
    
    def subscribe_to_device_topics(self, device_id: str) -> bool:
        """Subscribe to all relevant topics for a device"""
        device_topics = MQTTTopicManager.get_device_topics(device_id)
        success = True
        
        for topic_name, topic_path in device_topics.items():
            topic_structure = MQTTTopicManager.get_topic_structure(topic_name)
            
            # Only subscribe to topics that we should receive (not send)
            if topic_structure.topic_type in [TopicType.TELEMETRY, TopicType.STATUS]:
                if not self.subscribe(topic_path, qos=topic_structure.qos.value):
                    success = False
        
        return success
    
    def subscribe_to_system_topics(self) -> bool:
        """Subscribe to system-wide topics"""
        patterns = MQTTTopicManager.get_wildcard_patterns()
        success = True
        
        # Subscribe to key system topics
        system_topics = [
            "all_device_telemetry",
            "all_device_status",
            "all_system_topics",
            "all_discovery"
        ]
        
        for topic_name in system_topics:
            if topic_name in patterns:
                if not self.subscribe(patterns[topic_name]):
                    success = False
        
        return success
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful connection"""
        if rc == 0:
            self.connected = True
            self.logger.info("Successfully connected to MQTT broker")
            
            # Subscribe to system topics
            self.subscribe_to_system_topics()
            
        else:
            self.logger.error(f"Failed to connect to MQTT broker: {mqtt.connack_string(rc)}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for disconnection"""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected disconnection from MQTT broker: {mqtt.error_string(rc)}")
            
            # Attempt reconnection if enabled
            if self.config.auto_reconnect:
                self._attempt_reconnect()
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback for received messages"""
        try:
            # Create MQTT message object
            message = MQTTMessage(
                topic=msg.topic,
                payload=msg.payload.decode('utf-8') if isinstance(msg.payload, bytes) else msg.payload,
                qos=msg.qos,
                retain=msg.retain
            )
            
            # Route message to appropriate handlers
            handled = False
            for handler in self.message_handlers:
                if handler.can_handle(message.topic):
                    handler.handle_message(message)
                    handled = True
            
            # Call topic-specific callbacks
            for topic_pattern, callbacks in self.subscription_callbacks.items():
                if self._topic_matches_pattern(message.topic, topic_pattern):
                    for callback in callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            self.logger.error(f"Error in subscription callback: {e}")
            
            if not handled:
                self.logger.debug(f"No handler for topic: {message.topic}")
                
        except Exception as e:
            self.logger.error(f"Error processing received message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for successful publish"""
        self.logger.debug(f"Message published with mid: {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for successful subscription"""
        self.logger.debug(f"Subscription successful with mid: {mid}, QoS: {granted_qos}")
    
    def _on_log(self, client, userdata, level, buf):
        """Callback for MQTT client logs"""
        if level == mqtt.MQTT_LOG_DEBUG:
            self.logger.debug(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_INFO:
            self.logger.info(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            self.logger.warning(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_ERR:
            self.logger.error(f"MQTT: {buf}")
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches subscription pattern"""
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")
        
        if len(pattern_parts) != len(topic_parts):
            return False
        
        for pattern_part, topic_part in zip(pattern_parts, topic_parts):
            if pattern_part == "+":
                continue
            elif pattern_part == "#":
                return True
            elif pattern_part != topic_part:
                return False
        
        return True
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to the broker"""
        def reconnect_thread():
            retries = 0
            while retries < self.config.max_retries and not self.connected:
                try:
                    self.logger.info(f"Attempting to reconnect ({retries + 1}/{self.config.max_retries})")
                    if self.connect():
                        break
                except Exception as e:
                    self.logger.error(f"Reconnection attempt failed: {e}")
                
                retries += 1
                if retries < self.config.max_retries:
                    time.sleep(self.config.retry_delay)
            
            if not self.connected:
                self.logger.error("All reconnection attempts failed")
        
        thread = threading.Thread(target=reconnect_thread, daemon=True)
        thread.start()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and statistics"""
        return {
            "connected": self.connected,
            "host": self.config.host,
            "port": self.config.port,
            "client_id": self.config.client_id,
            "use_tls": self.config.use_tls,
            "handlers_count": len(self.message_handlers),
            "subscriptions_count": len(self.subscription_callbacks)
        }


# Factory function to create MQTT client service
def create_mqtt_service(config: Dict[str, Any]) -> MQTTClientService:
    """
    Factory function to create MQTT client service from configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured MQTT client service
    """
    mqtt_config = MQTTConfig(
        host=config.get("host", "localhost"),
        port=config.get("port", 1883),
        keepalive=config.get("keepalive", 60),
        username=config.get("username"),
        password=config.get("password"),
        client_id=config.get("client_id"),
        clean_session=config.get("clean_session", True),
        use_tls=config.get("use_tls", False),
        tls_port=config.get("tls_port", 8883),
        ca_cert_path=config.get("ca_cert_path"),
        cert_file_path=config.get("cert_file_path"),
        key_file_path=config.get("key_file_path"),
        tls_insecure=config.get("tls_insecure", False),
        max_retries=config.get("max_retries", 5),
        retry_delay=config.get("retry_delay", 5),
        auto_reconnect=config.get("auto_reconnect", True),
        max_inflight_messages=config.get("max_inflight_messages", 20),
        message_retry_set=config.get("message_retry_set", 20),
        default_qos=config.get("default_qos", 1)
    )
    
    return MQTTClientService(mqtt_config)
