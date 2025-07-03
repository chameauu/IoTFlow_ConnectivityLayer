"""
Advanced monitoring and health check middleware
"""

import time
import psutil
import redis
from flask import current_app, jsonify, request
from functools import wraps
from src.models import Device, db
from datetime import datetime, timezone, timedelta


class HealthMonitor:
    """System health monitoring service"""
    
    @staticmethod
    def get_system_health():
        """Get comprehensive system health status"""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {},
            'metrics': {}
        }
        
        try:
            # Database health
            health_data['checks']['database'] = HealthMonitor._check_database()
            
            # Redis health
            health_data['checks']['redis'] = HealthMonitor._check_redis()
            
            # IoTDB health
            health_data['checks']['iotdb'] = HealthMonitor._check_iotdb()
            
            # System metrics
            health_data['metrics']['system'] = HealthMonitor._get_system_metrics()
            
            # Application metrics
            health_data['metrics']['application'] = HealthMonitor._get_app_metrics()
            
            # Device status summary
            health_data['metrics']['devices'] = HealthMonitor._get_device_metrics()
            
            # Determine overall status
            failed_checks = [name for name, check in health_data['checks'].items() 
                           if not check.get('healthy', False)]
            
            if failed_checks:
                health_data['status'] = 'degraded' if len(failed_checks) == 1 else 'unhealthy'
                health_data['failed_checks'] = failed_checks
            
        except Exception as e:
            health_data['status'] = 'error'
            health_data['error'] = str(e)
            current_app.logger.error(f"Health check error: {str(e)}")
        
        return health_data
    
    @staticmethod
    def _check_database():
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            response_time = (time.time() - start_time) * 1000  # ms
            
            return {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'status': 'connected'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'disconnected'
            }
    
    @staticmethod
    def _check_redis():
        """Check Redis connectivity and performance"""
        try:
            if hasattr(current_app, 'redis_client'):
                start_time = time.time()
                current_app.redis_client.ping()
                response_time = (time.time() - start_time) * 1000  # ms
                
                # Get Redis info
                info = current_app.redis_client.info()
                
                return {
                    'healthy': True,
                    'response_time_ms': round(response_time, 2),
                    'status': 'connected',
                    'memory_usage_mb': round(info.get('used_memory', 0) / 1024 / 1024, 2),
                    'connected_clients': info.get('connected_clients', 0)
                }
            else:
                return {
                    'healthy': False,
                    'status': 'not_configured',
                    'message': 'Redis client not configured'
                }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'disconnected'
            }
    
    @staticmethod
    def _check_iotdb():
        """Check IoTDB connectivity and performance"""
        try:
            from src.config.iotdb_config import iotdb_config
            
            start_time = time.time()
            is_connected = iotdb_config.is_connected()
            response_time = (time.time() - start_time) * 1000  # ms
            
            if is_connected and iotdb_config.session:
                # Test basic query to ensure IoTDB is responsive
                try:
                    query_start = time.time()
                    # Simple test query - check if we can execute basic operations
                    session_data_set = iotdb_config.session.execute_query_statement("SHOW DATABASES")
                    query_time = (time.time() - query_start) * 1000
                    session_data_set.close_operation_handle()
                    
                    return {
                        'healthy': True,
                        'response_time_ms': round(response_time, 2),
                        'query_time_ms': round(query_time, 2),
                        'status': 'connected',
                        'host': iotdb_config.host,
                        'port': iotdb_config.port,
                        'database': iotdb_config.database
                    }
                except Exception as query_error:
                    return {
                        'healthy': False,
                        'status': 'connected_but_unresponsive',
                        'error': f"Query failed: {str(query_error)}",
                        'response_time_ms': round(response_time, 2)
                    }
            else:
                return {
                    'healthy': False,
                    'status': 'disconnected',
                    'error': 'IoTDB session not available',
                    'host': iotdb_config.host,
                    'port': iotdb_config.port
                }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'error'
            }
    
    @staticmethod
    def _get_system_metrics():
        """Get system performance metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available_mb': round(psutil.virtual_memory().available / 1024 / 1024, 2),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            current_app.logger.error(f"System metrics error: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def _get_app_metrics():
        """Get application-specific metrics"""
        try:
            # Get uptime (approximate)
            return {
                'flask_env': current_app.config.get('ENV'),
                'debug_mode': current_app.debug,
                'testing_mode': current_app.testing
            }
        except Exception as e:
            current_app.logger.error(f"App metrics error: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def _get_device_metrics():
        """Get device-related metrics"""
        try:
            now = datetime.now(timezone.utc)
            online_threshold = now - timedelta(minutes=5)
            
            total_devices = Device.query.count()
            active_devices = Device.query.filter_by(status='active').count()
            online_devices = Device.query.filter(
                Device.last_seen >= online_threshold,
                Device.status == 'active'
            ).count()
            
            # Telemetry metrics (now stored in IoTDB)
            telemetry_last_hour = HealthMonitor._get_telemetry_count_iotdb('-1h')
            telemetry_last_day = HealthMonitor._get_telemetry_count_iotdb('-1d')
            
            return {
                'total_devices': total_devices,
                'active_devices': active_devices,
                'online_devices': online_devices,
                'offline_devices': active_devices - online_devices,
                'telemetry_last_hour': telemetry_last_hour,
                'telemetry_last_day': telemetry_last_day
            }
        except Exception as e:
            try:
                current_app.logger.error(f"Device metrics error: {str(e)}")
            except:
                # Fallback if current_app is not available
                print(f"Device metrics error: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def _get_telemetry_count_iotdb(time_range: str) -> int:
        """Get telemetry count from IoTDB for specified time range"""
        try:
            from src.config.iotdb_config import iotdb_config
            from datetime import datetime, timezone
            
            if not iotdb_config.is_connected():
                return 0
            
            # For now, return total count regardless of time range
            # TODO: Implement proper time-based filtering when IoTDB query syntax is clarified
            query = f"SHOW TIMESERIES {iotdb_config.database}.devices.**"
            
            session_data_set = iotdb_config.session.execute_query_statement(query)
            
            timeseries_count = 0
            while session_data_set.has_next():
                record = session_data_set.next()
                timeseries_count += 1
            
            session_data_set.close_operation_handle()
            
            # Rough estimate: assume each timeseries has some data points
            # This is a simplified approach until proper count aggregation is implemented
            return timeseries_count
            
        except Exception as e:
            try:
                current_app.logger.error(f"Error getting telemetry count from IoTDB: {str(e)}")
            except:
                # Fallback if current_app is not available
                print(f"Error getting telemetry count from IoTDB: {str(e)}")
            return 0


def device_heartbeat_monitor():
    """Monitor device heartbeats and update status"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if hasattr(request, 'device'):
                device = request.device
                
                # Update device heartbeat in Redis
                if hasattr(current_app, 'redis_client'):
                    try:
                        current_app.redis_client.setex(
                            f"heartbeat:{device.id}", 
                            300,  # 5 minutes TTL
                            "online"
                        )
                    except Exception as e:
                        current_app.logger.error(f"Redis heartbeat error: {str(e)}")
                
                # Update last_seen in database
                device.update_last_seen()
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def request_metrics_middleware():
    """Middleware to collect request metrics"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Execute request
            try:
                response = f(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                success = True
            except Exception as e:
                response = jsonify({'error': 'Internal server error'}), 500
                status_code = 500
                success = False
                current_app.logger.error(f"Request error: {str(e)}")
            
            # Calculate metrics
            duration = time.time() - start_time
            
            # Log metrics
            current_app.logger.info(
                f"REQUEST_METRICS: {request.method} {request.path} "
                f"status={status_code} duration={duration:.3f}s "
                f"success={success} ip={request.remote_addr}"
            )
            
            # Store metrics in Redis if available
            if hasattr(current_app, 'redis_client'):
                try:
                    metrics_key = f"metrics:{request.method}:{request.endpoint or 'unknown'}"
                    current_app.redis_client.lpush(metrics_key, f"{status_code}:{duration:.3f}")
                    current_app.redis_client.ltrim(metrics_key, 0, 999)  # Keep last 1000 entries
                except Exception as e:
                    current_app.logger.error(f"Metrics storage error: {str(e)}")
            
            return response
        
        return decorated_function
    return decorator
