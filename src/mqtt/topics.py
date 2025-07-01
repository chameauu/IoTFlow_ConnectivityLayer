"""
MQTT Topic Architecture for IoTFlow
Defines the hierarchical topic structure and naming conventions
"""

import re
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class QoSLevel(Enum):
    """MQTT Quality of Service levels"""
    AT_MOST_ONCE = 0    # Fire and forget
    AT_LEAST_ONCE = 1   # Acknowledged delivery
    EXACTLY_ONCE = 2    # Assured delivery


class TopicType(Enum):
    """Types of MQTT topics in the IoTFlow system"""
    TELEMETRY = "telemetry"
    COMMANDS = "commands"
    STATUS = "status"
    CONFIG = "config"
    DISCOVERY = "discovery"
    SYSTEM = "system"
    FLEET = "fleet"
    MONITORING = "monitoring"
    ALERTS = "alerts"
    LWT = "lwt"  # Last Will and Testament


@dataclass
class TopicStructure:
    """Defines the structure of an MQTT topic"""
    base_path: str
    topic_type: TopicType
    qos: QoSLevel
    retain: bool = False
    description: str = ""


class MQTTTopicManager:
    """
    Manages MQTT topic structure and naming conventions for IoTFlow
    
    Topic Hierarchy:
    iotflow/
    ├── devices/
    │   ├── {device_id}/
    │   │   ├── telemetry/
    │   │   │   ├── sensors/
    │   │   │   ├── metrics/
    │   │   │   └── events/
    │   │   ├── commands/
    │   │   │   ├── config/
    │   │   │   ├── control/
    │   │   │   └── firmware/
    │   │   ├── status/
    │   │   │   ├── heartbeat
    │   │   │   ├── online
    │   │   │   └── offline
    │   │   └── config/
    │   └── discovery/
    ├── fleet/
    │   ├── commands/
    │   ├── status/
    │   └── groups/
    ├── system/
    │   ├── health/
    │   ├── metrics/
    │   └── alerts/
    └── monitoring/
        ├── broker/
        ├── clients/
        └── traffic/
    """
    
    BASE_TOPIC = "iotflow"
    
    # Topic structure definitions
    TOPIC_STRUCTURES = {
        # Device-specific topics
        "device_telemetry_sensors": TopicStructure(
            base_path="devices/{device_id}/telemetry/sensors",
            topic_type=TopicType.TELEMETRY,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=False,
            description="Sensor data from devices"
        ),
        "device_telemetry_metrics": TopicStructure(
            base_path="devices/{device_id}/telemetry/metrics",
            topic_type=TopicType.TELEMETRY,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=False,
            description="Device performance metrics"
        ),
        "device_telemetry_events": TopicStructure(
            base_path="devices/{device_id}/telemetry/events",
            topic_type=TopicType.TELEMETRY,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=False,
            description="Device events and alerts"
        ),
        "device_commands_config": TopicStructure(
            base_path="devices/{device_id}/commands/config",
            topic_type=TopicType.COMMANDS,
            qos=QoSLevel.EXACTLY_ONCE,
            retain=True,
            description="Configuration commands for devices"
        ),
        "device_commands_control": TopicStructure(
            base_path="devices/{device_id}/commands/control",
            topic_type=TopicType.COMMANDS,
            qos=QoSLevel.EXACTLY_ONCE,
            retain=False,
            description="Control commands for devices"
        ),
        "device_commands_firmware": TopicStructure(
            base_path="devices/{device_id}/commands/firmware",
            topic_type=TopicType.COMMANDS,
            qos=QoSLevel.EXACTLY_ONCE,
            retain=True,
            description="Firmware update commands"
        ),
        "device_status_heartbeat": TopicStructure(
            base_path="devices/{device_id}/status/heartbeat",
            topic_type=TopicType.STATUS,
            qos=QoSLevel.AT_MOST_ONCE,
            retain=False,
            description="Device heartbeat messages"
        ),
        "device_status_online": TopicStructure(
            base_path="devices/{device_id}/status/online",
            topic_type=TopicType.STATUS,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=True,
            description="Device online status"
        ),
        "device_status_offline": TopicStructure(
            base_path="devices/{device_id}/status/offline",
            topic_type=TopicType.STATUS,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=True,
            description="Device offline status"
        ),
        "device_config": TopicStructure(
            base_path="devices/{device_id}/config",
            topic_type=TopicType.CONFIG,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=True,
            description="Device configuration settings"
        ),
        "device_lwt": TopicStructure(
            base_path="lwt/devices/{device_id}",
            topic_type=TopicType.LWT,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=True,
            description="Last Will and Testament for devices"
        ),
        
        # Discovery topics
        "discovery_register": TopicStructure(
            base_path="discovery/register/{device_id}",
            topic_type=TopicType.DISCOVERY,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=False,
            description="Device registration requests"
        ),
        "discovery_response": TopicStructure(
            base_path="discovery/response/{device_id}",
            topic_type=TopicType.DISCOVERY,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=False,
            description="Registration response messages"
        ),
        
        # Fleet management topics
        "fleet_commands": TopicStructure(
            base_path="fleet/commands/{group_id}",
            topic_type=TopicType.COMMANDS,
            qos=QoSLevel.EXACTLY_ONCE,
            retain=True,
            description="Commands for device groups"
        ),
        "fleet_status": TopicStructure(
            base_path="fleet/status/{group_id}",
            topic_type=TopicType.STATUS,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=True,
            description="Status of device groups"
        ),
        
        # System topics
        "system_health": TopicStructure(
            base_path="system/health",
            topic_type=TopicType.SYSTEM,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=True,
            description="System health status"
        ),
        "system_metrics": TopicStructure(
            base_path="system/metrics",
            topic_type=TopicType.SYSTEM,
            qos=QoSLevel.AT_MOST_ONCE,
            retain=False,
            description="System performance metrics"
        ),
        "system_alerts": TopicStructure(
            base_path="system/alerts",
            topic_type=TopicType.ALERTS,
            qos=QoSLevel.AT_LEAST_ONCE,
            retain=True,
            description="System alerts and notifications"
        ),
        
        # Monitoring topics
        "monitoring_broker": TopicStructure(
            base_path="monitoring/broker",
            topic_type=TopicType.MONITORING,
            qos=QoSLevel.AT_MOST_ONCE,
            retain=False,
            description="MQTT broker monitoring data"
        ),
        "monitoring_clients": TopicStructure(
            base_path="monitoring/clients",
            topic_type=TopicType.MONITORING,
            qos=QoSLevel.AT_MOST_ONCE,
            retain=False,
            description="MQTT client monitoring data"
        ),
        "monitoring_traffic": TopicStructure(
            base_path="monitoring/traffic",
            topic_type=TopicType.MONITORING,
            qos=QoSLevel.AT_MOST_ONCE,
            retain=False,
            description="MQTT traffic monitoring data"
        ),
    }
    
    @classmethod
    def get_topic(cls, topic_name: str, **kwargs) -> str:
        """
        Get a fully qualified topic path
        
        Args:
            topic_name: Name of the topic structure
            **kwargs: Parameters to format into the topic path
            
        Returns:
            Formatted topic path
            
        Raises:
            KeyError: If topic_name is not found
            ValueError: If required parameters are missing
        """
        if topic_name not in cls.TOPIC_STRUCTURES:
            raise KeyError(f"Topic '{topic_name}' not found in topic structures")
        
        structure = cls.TOPIC_STRUCTURES[topic_name]
        
        try:
            formatted_path = structure.base_path.format(**kwargs)
            return f"{cls.BASE_TOPIC}/{formatted_path}"
        except KeyError as e:
            raise ValueError(f"Missing required parameter for topic '{topic_name}': {e}")
    
    @classmethod
    def get_topic_structure(cls, topic_name: str) -> TopicStructure:
        """Get the topic structure definition"""
        if topic_name not in cls.TOPIC_STRUCTURES:
            raise KeyError(f"Topic '{topic_name}' not found in topic structures")
        return cls.TOPIC_STRUCTURES[topic_name]
    
    @classmethod
    def get_device_topics(cls, device_id: str) -> Dict[str, str]:
        """Get all device-specific topics for a given device ID"""
        device_topics = {}
        for topic_name, structure in cls.TOPIC_STRUCTURES.items():
            if "{device_id}" in structure.base_path:
                device_topics[topic_name] = cls.get_topic(topic_name, device_id=device_id)
        return device_topics
    
    @classmethod
    def get_fleet_topics(cls, group_id: str) -> Dict[str, str]:
        """Get all fleet management topics for a given group ID"""
        fleet_topics = {}
        for topic_name, structure in cls.TOPIC_STRUCTURES.items():
            if "fleet" in structure.base_path and "{group_id}" in structure.base_path:
                fleet_topics[topic_name] = cls.get_topic(topic_name, group_id=group_id)
        return fleet_topics
    
    @classmethod
    def get_wildcard_patterns(cls) -> Dict[str, str]:
        """Get wildcard subscription patterns for different purposes"""
        patterns = {
            "all_device_telemetry": f"{cls.BASE_TOPIC}/devices/+/telemetry/+",
            "all_device_status": f"{cls.BASE_TOPIC}/devices/+/status/+",
            "all_device_commands": f"{cls.BASE_TOPIC}/devices/+/commands/+",
            "all_fleet_commands": f"{cls.BASE_TOPIC}/fleet/commands/+",
            "all_system_topics": f"{cls.BASE_TOPIC}/system/+",
            "all_monitoring": f"{cls.BASE_TOPIC}/monitoring/+",
            "all_discovery": f"{cls.BASE_TOPIC}/discovery/+/+",
            "everything": f"{cls.BASE_TOPIC}/#"
        }
        return patterns
    
    @classmethod
    def validate_topic(cls, topic: str) -> bool:
        """
        Validate if a topic follows IoTFlow naming conventions
        
        Args:
            topic: Topic to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not topic.startswith(f"{cls.BASE_TOPIC}/"):
            return False
        
        # Check for invalid characters
        invalid_chars = ["+", "#", "\0"]
        for char in invalid_chars:
            if char in topic.replace(f"{cls.BASE_TOPIC}/", ""):
                return False
        
        # Check topic length (MQTT spec limit)
        if len(topic.encode('utf-8')) > 65535:
            return False
        
        return True
    
    @classmethod
    def parse_topic(cls, topic: str) -> Optional[Dict[str, str]]:
        """
        Parse a topic and extract components
        
        Args:
            topic: Topic to parse
            
        Returns:
            Dictionary with topic components or None if invalid
        """
        if not cls.validate_topic(topic):
            return None
        
        # Remove base topic
        topic_path = topic.replace(f"{cls.BASE_TOPIC}/", "")
        parts = topic_path.split("/")
        
        parsed = {
            "base": cls.BASE_TOPIC,
            "full_topic": topic,
            "path": topic_path,
            "parts": parts
        }
        
        # Extract common patterns
        if len(parts) >= 2:
            parsed["category"] = parts[0]  # devices, fleet, system, etc.
            
            if parts[0] == "devices" and len(parts) >= 3:
                parsed["device_id"] = parts[1]
                parsed["topic_type"] = parts[2]
                if len(parts) >= 4:
                    parsed["subtopic"] = parts[3]
            
            elif parts[0] == "fleet" and len(parts) >= 3:
                parsed["topic_type"] = parts[1]
                parsed["group_id"] = parts[2]
            
            elif parts[0] == "system" and len(parts) >= 2:
                parsed["topic_type"] = parts[1]
        
        return parsed
