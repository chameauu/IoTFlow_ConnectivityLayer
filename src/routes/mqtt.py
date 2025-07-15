"""
MQTT API Routes for IoTFlow
Provides REST endpoints for MQTT management and monitoring
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any
import json
from datetime import datetime

from ..middleware.auth import authenticate_device,require_admin_token
from ..middleware.monitoring import request_metrics_middleware
from ..middleware.security import security_headers_middleware, input_sanitization_middleware
from ..mqtt.topics import MQTTTopicManager
from ..utils.logging import get_logger

mqtt_bp = Blueprint('mqtt', __name__, url_prefix='/api/v1/mqtt')
logger = get_logger(__name__)


@mqtt_bp.route('/status', methods=['GET'])
def get_mqtt_status():
    """Get MQTT broker and client status"""
    try:
        mqtt_service = getattr(current_app, 'mqtt_service', None)
        
        if not mqtt_service:
            return jsonify({
                'error': 'MQTT service not initialized',
                'status': 'unavailable'
            }), 503
        
        status = mqtt_service.get_connection_status()
        
        return jsonify({
            'status': 'success',
            'mqtt_status': status,
            'broker_info': {
                'host': status['host'],
                'port': status['port'],
                'connected': status['connected'],
                'tls_enabled': status['use_tls']
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting MQTT status: {e}")
        return jsonify({
            'error': 'Failed to get MQTT status',
            'message': str(e)
        }), 500


@mqtt_bp.route('/publish', methods=['POST'])
def publish_message():
    """Publish a message to MQTT broker"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['topic', 'payload']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        topic = data['topic']
        payload = data['payload']
        qos = data.get('qos', 1)
        retain = data.get('retain', False)
        
        # Validate topic
        if not MQTTTopicManager.validate_topic(topic):
            return jsonify({
                'error': 'Invalid topic format',
                'topic': topic
            }), 400
        
        # Get MQTT service
        mqtt_service = getattr(current_app, 'mqtt_service', None)
        if not mqtt_service:
            return jsonify({
                'error': 'MQTT service not available'
            }), 503
        
        # Publish message
        success = mqtt_service.publish(topic, payload, qos=qos, retain=retain)
        
        if success:
            logger.info(f"Published message to topic: {topic}")
            return jsonify({
                'status': 'success',
                'message': 'Message published successfully',
                'topic': topic,
                'qos': qos,
                'retain': retain
            })
        else:
            return jsonify({
                'error': 'Failed to publish message',
                'topic': topic
            }), 500
            
    except Exception as e:
        logger.error(f"Error publishing MQTT message: {e}")
        return jsonify({
            'error': 'Failed to publish message',
            'message': str(e)
        }), 500


@mqtt_bp.route('/subscribe', methods=['POST'])
def subscribe_to_topic():
    """Subscribe to an MQTT topic (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'topic' not in data:
            return jsonify({
                'error': 'Missing required field: topic'
            }), 400
        
        topic = data['topic']
        qos = data.get('qos', 1)
        
        # Get MQTT service
        mqtt_service = getattr(current_app, 'mqtt_service', None)
        if not mqtt_service:
            return jsonify({
                'error': 'MQTT service not available'
            }), 503
        
        # Subscribe to topic
        success = mqtt_service.subscribe(topic, qos=qos)
        
        if success:
            logger.info(f"Subscribed to topic: {topic}")
            return jsonify({
                'status': 'success',
                'message': 'Subscribed successfully',
                'topic': topic,
                'qos': qos
            })
        else:
            return jsonify({
                'error': 'Failed to subscribe to topic',
                'topic': topic
            }), 500
            
    except Exception as e:
        logger.error(f"Error subscribing to MQTT topic: {e}")
        return jsonify({
            'error': 'Failed to subscribe',
            'message': str(e)
        }), 500


@mqtt_bp.route('/topics/device/<device_id>', methods=['GET'])
def get_device_topics(device_id: str):
    """Get all MQTT topics for a specific device"""
    try:
        # Validate device_id format
        if not device_id or len(device_id) < 3:
            return jsonify({
                'error': 'Invalid device ID format'
            }), 400
        
        # Get device topics
        device_topics = MQTTTopicManager.get_device_topics(device_id)
        
        # Organize topics by type
        organized_topics = {}
        for topic_name, topic_path in device_topics.items():
            topic_structure = MQTTTopicManager.get_topic_structure(topic_name)
            topic_type = topic_structure.topic_type.value
            
            if topic_type not in organized_topics:
                organized_topics[topic_type] = []
            
            organized_topics[topic_type].append({
                'name': topic_name,
                'path': topic_path,
                'qos': topic_structure.qos.value,
                'retain': topic_structure.retain,
                'description': topic_structure.description
            })
        
        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'topics': organized_topics,
            'total_topics': len(device_topics)
        })
        
    except Exception as e:
        logger.error(f"Error getting device topics: {e}")
        return jsonify({
            'error': 'Failed to get device topics',
            'message': str(e)
        }), 500


@mqtt_bp.route('/topics/structure', methods=['GET'])
def get_topic_structure():
    """Get the complete MQTT topic structure"""
    try:
        # Get wildcard patterns
        patterns = MQTTTopicManager.get_wildcard_patterns()
        
        # Get all topic structures
        structures = {}
        for topic_name, structure in MQTTTopicManager.TOPIC_STRUCTURES.items():
            structures[topic_name] = {
                'base_path': structure.base_path,
                'topic_type': structure.topic_type.value,
                'qos': structure.qos.value,
                'retain': structure.retain,
                'description': structure.description,
                'full_topic_example': f"{MQTTTopicManager.BASE_TOPIC}/{structure.base_path}"
            }
        
        return jsonify({
            'status': 'success',
            'base_topic': MQTTTopicManager.BASE_TOPIC,
            'wildcard_patterns': patterns,
            'topic_structures': structures,
            'total_structures': len(structures)
        })
        
    except Exception as e:
        logger.error(f"Error getting topic structure: {e}")
        return jsonify({
            'error': 'Failed to get topic structure',
            'message': str(e)
        }), 500


@mqtt_bp.route('/topics/validate', methods=['POST'])
def validate_topic():
    """Validate an MQTT topic"""
    try:
        data = request.get_json()
        
        if 'topic' not in data:
            return jsonify({
                'error': 'Missing required field: topic'
            }), 400
        
        topic = data['topic']
        
        # Validate topic
        is_valid = MQTTTopicManager.validate_topic(topic)
        parsed_topic = MQTTTopicManager.parse_topic(topic) if is_valid else None
        
        response = {
            'status': 'success',
            'topic': topic,
            'is_valid': is_valid,
            'parsed': parsed_topic
        }
        
        if not is_valid:
            response['validation_errors'] = []
            
            # Check specific validation issues
            if not topic.startswith(f"{MQTTTopicManager.BASE_TOPIC}/"):
                response['validation_errors'].append(
                    f"Topic must start with '{MQTTTopicManager.BASE_TOPIC}/'"
                )
            
            if len(topic.encode('utf-8')) > 65535:
                response['validation_errors'].append("Topic too long (max 65535 bytes)")
            
            invalid_chars = ["+", "#", "\0"]
            for char in invalid_chars:
                if char in topic.replace(f"{MQTTTopicManager.BASE_TOPIC}/", ""):
                    response['validation_errors'].append(f"Invalid character: '{char}'")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error validating topic: {e}")
        return jsonify({
            'error': 'Failed to validate topic',
            'message': str(e)
        }), 500


@mqtt_bp.route('/device/<device_id>/command', methods=['POST'])
@require_admin_token
def send_device_command(device_id: str):
    """Send a command to a specific device via MQTT"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['command_type', 'command']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        command_type = data['command_type']
        command = data['command']
        qos = data.get('qos', 2)  # Use QoS 2 for commands to ensure delivery
        
        # Validate command type
        valid_command_types = ['config', 'control', 'firmware']
        if command_type not in valid_command_types:
            return jsonify({
                'error': f'Invalid command type. Must be one of: {valid_command_types}'
            }), 400
        
        # Get command topic
        topic_name = f"device_commands_{command_type}"
        try:
            topic = MQTTTopicManager.get_topic(topic_name, device_id=device_id)
        except (KeyError, ValueError) as e:
            return jsonify({
                'error': f'Invalid topic configuration: {str(e)}'
            }), 400
        
        # Prepare command payload
        command_payload = {
            'command': command,
            'timestamp': data.get('timestamp'),
            'command_id': data.get('command_id'),
            'source': 'iotflow_api'
        }
        
        # Get MQTT service
        mqtt_service = getattr(current_app, 'mqtt_service', None)
        if not mqtt_service:
            return jsonify({
                'error': 'MQTT service not available'
            }), 503
        
        # Send command
        success = mqtt_service.publish(topic, command_payload, qos=qos, retain=True)
        
        if success:
            logger.info(f"Sent {command_type} command to device {device_id}")
            return jsonify({
                'status': 'success',
                'message': 'Command sent successfully',
                'device_id': device_id,
                'command_type': command_type,
                'topic': topic,
                'qos': qos
            })
        else:
            return jsonify({
                'error': 'Failed to send command',
                'device_id': device_id,
                'command_type': command_type
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending device command: {e}")
        return jsonify({
            'error': 'Failed to send command',
            'message': str(e)
        }), 500


@mqtt_bp.route('/fleet/<group_id>/command', methods=['POST'])
def send_fleet_command(group_id: str):
    """Send a command to a fleet/group of devices via MQTT (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'command' not in data:
            return jsonify({
                'error': 'Missing required field: command'
            }), 400
        
        command = data['command']
        qos = data.get('qos', 2)
        
        # Get fleet command topic
        try:
            topic = MQTTTopicManager.get_topic('fleet_commands', group_id=group_id)
        except (KeyError, ValueError) as e:
            return jsonify({
                'error': f'Invalid topic configuration: {str(e)}'
            }), 400
        
        # Prepare command payload
        command_payload = {
            'command': command,
            'timestamp': data.get('timestamp'),
            'command_id': data.get('command_id'),
            'group_id': group_id,
            'source': 'iotflow_api'
        }
        
        # Get MQTT service
        mqtt_service = getattr(current_app, 'mqtt_service', None)
        if not mqtt_service:
            return jsonify({
                'error': 'MQTT service not available'
            }), 503
        
        # Send fleet command
        success = mqtt_service.publish(topic, command_payload, qos=qos, retain=True)
        
        if success:
            logger.info(f"Sent fleet command to group {group_id}")
            return jsonify({
                'status': 'success',
                'message': 'Fleet command sent successfully',
                'group_id': group_id,
                'topic': topic,
                'qos': qos
            })
        else:
            return jsonify({
                'error': 'Failed to send fleet command',
                'group_id': group_id
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending fleet command: {e}")
        return jsonify({
            'error': 'Failed to send fleet command',
            'message': str(e)
        }), 500


@mqtt_bp.route('/monitoring/metrics', methods=['GET'])
@require_admin_token
def get_mqtt_metrics():
    """Get MQTT monitoring metrics (admin only)"""
    try:
        mqtt_service = getattr(current_app, 'mqtt_service', None)
        if not mqtt_service:
            return jsonify({
                'error': 'MQTT service not available'
            }), 503
        
        # Get connection status
        status = mqtt_service.get_connection_status()
        
        # TODO: Add more detailed metrics from broker
        # This would require implementing broker monitoring features
        
        metrics = {
            'connection_status': status,
            'topics': {
                'total_structures': len(MQTTTopicManager.TOPIC_STRUCTURES),
                'base_topic': MQTTTopicManager.BASE_TOPIC
            },
            'handlers': {
                'message_handlers': len(mqtt_service.message_handlers),
                'subscription_callbacks': len(mqtt_service.subscription_callbacks)
            }
        }
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting MQTT metrics: {e}")
        return jsonify({
            'error': 'Failed to get MQTT metrics',
            'message': str(e)
        }), 500


@mqtt_bp.route('/telemetry/<int:device_id>', methods=['POST'])
@security_headers_middleware()
@request_metrics_middleware()
@input_sanitization_middleware()
def mqtt_telemetry(device_id):
    """
    MQTT Telemetry endpoint with API key authentication
    This endpoint accepts telemetry data from devices and validates API key server-side
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get API key from headers
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Include X-API-Key header with your device API key'
            }), 401
        
        # Get MQTT auth service
        mqtt_auth_service = getattr(current_app, 'mqtt_auth_service', None)
        if not mqtt_auth_service:
            return jsonify({
                'error': 'MQTT authentication service not available'
            }), 503
        
        # Validate device and API key
        device = mqtt_auth_service.authenticate_device_by_api_key(api_key)
        if not device or device.id != device_id:
            return jsonify({
                'error': 'Invalid API key or device ID mismatch',
                'device_id': device_id
            }), 401
        
        # Extract telemetry data
        telemetry_data = data.get('data', {})
        metadata = data.get('metadata', {})
        timestamp_str = data.get('timestamp')
        
        if not telemetry_data:
            return jsonify({
                'error': 'Telemetry data is required',
                'message': 'Include "data" field with sensor readings'
            }), 400
        
        # Create MQTT topic for telemetry
        topic = f"iotflow/devices/{device_id}/telemetry"
        
        # Handle telemetry message through MQTT auth service
        success = mqtt_auth_service.handle_telemetry_message(
            device_id=device_id,
            api_key=api_key,
            topic=topic,
            payload=json.dumps(data)
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Telemetry data processed successfully',
                'device_id': device_id,
                'device_name': device.name,
                'topic': topic,
                'timestamp': timestamp_str or datetime.utcnow().isoformat()
            }), 201
        else:
            return jsonify({
                'error': 'Failed to process telemetry data',
                'message': 'Check device authorization and data format'
            }), 400
            
    except Exception as e:
        logger.error(f"Error processing MQTT telemetry: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to process telemetry data'
        }), 500
