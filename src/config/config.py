import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///iotflow.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # InfluxDB Configuration
    INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'http://localhost:8086')
    INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'your-super-secret-token')
    INFLUXDB_ORG = os.environ.get('INFLUXDB_ORG', 'iotflow')
    INFLUXDB_BUCKET = os.environ.get('INFLUXDB_BUCKET', 'telemetry')
    
    # API Configuration
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    MAX_DEVICES_PER_USER = int(os.environ.get('MAX_DEVICES_PER_USER', 100))
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60))
    
    # Security
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    API_KEY_LENGTH = int(os.environ.get('API_KEY_LENGTH', 32))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/iotflow.log')
    
    # MQTT Configuration (Server connects anonymously)
    MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
    MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
    MQTT_TLS_PORT = int(os.environ.get('MQTT_TLS_PORT', 8883))
    MQTT_WEBSOCKET_PORT = int(os.environ.get('MQTT_WEBSOCKET_PORT', 9001))
    # Note: No username/password - server connects anonymously to MQTT broker
    MQTT_CLIENT_ID = os.environ.get('MQTT_CLIENT_ID', 'iotflow_server')
    MQTT_KEEPALIVE = int(os.environ.get('MQTT_KEEPALIVE', 60))
    MQTT_CLEAN_SESSION = os.environ.get('MQTT_CLEAN_SESSION', 'True').lower() == 'true'
    
    # MQTT TLS/SSL Configuration
    MQTT_USE_TLS = os.environ.get('MQTT_USE_TLS', 'False').lower() == 'true'
    MQTT_CA_CERT_PATH = os.environ.get('MQTT_CA_CERT_PATH')
    MQTT_CERT_FILE_PATH = os.environ.get('MQTT_CERT_FILE_PATH')
    MQTT_KEY_FILE_PATH = os.environ.get('MQTT_KEY_FILE_PATH')
    MQTT_TLS_INSECURE = os.environ.get('MQTT_TLS_INSECURE', 'False').lower() == 'true'
    
    # MQTT Connection Settings
    MQTT_MAX_RETRIES = int(os.environ.get('MQTT_MAX_RETRIES', 5))
    MQTT_RETRY_DELAY = int(os.environ.get('MQTT_RETRY_DELAY', 5))
    MQTT_AUTO_RECONNECT = os.environ.get('MQTT_AUTO_RECONNECT', 'True').lower() == 'true'
    MQTT_MAX_INFLIGHT_MESSAGES = int(os.environ.get('MQTT_MAX_INFLIGHT_MESSAGES', 20))
    MQTT_MESSAGE_RETRY_SET = int(os.environ.get('MQTT_MESSAGE_RETRY_SET', 20))
    MQTT_DEFAULT_QOS = int(os.environ.get('MQTT_DEFAULT_QOS', 1))
    
    @property
    def mqtt_config(self):
        """Get MQTT configuration as dictionary for anonymous connection"""
        return {
            'host': self.MQTT_HOST,
            'port': self.MQTT_PORT,
            'keepalive': self.MQTT_KEEPALIVE,
            'username': None,  # Anonymous connection
            'password': None,  # Anonymous connection
            'client_id': self.MQTT_CLIENT_ID,
            'clean_session': self.MQTT_CLEAN_SESSION,
            'use_tls': self.MQTT_USE_TLS,
            'tls_port': self.MQTT_TLS_PORT,
            'ca_cert_path': self.MQTT_CA_CERT_PATH,
            'cert_file_path': self.MQTT_CERT_FILE_PATH,
            'key_file_path': self.MQTT_KEY_FILE_PATH,
            'tls_insecure': self.MQTT_TLS_INSECURE,
            'max_retries': self.MQTT_MAX_RETRIES,
            'retry_delay': self.MQTT_RETRY_DELAY,
            'auto_reconnect': self.MQTT_AUTO_RECONNECT,
            'max_inflight_messages': self.MQTT_MAX_INFLIGHT_MESSAGES,
            'message_retry_set': self.MQTT_MESSAGE_RETRY_SET,
            'default_qos': self.MQTT_DEFAULT_QOS
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
