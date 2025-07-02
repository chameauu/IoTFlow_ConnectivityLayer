from flask import Blueprint, request, jsonify, current_app
from src.models import Device, db
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, desc

# Create blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

@admin_bp.route('/devices', methods=['GET'])
def list_all_devices():
    """List all devices with filtering and pagination"""
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)  # Max 100 per page
        status = request.args.get('status')
        device_type = request.args.get('type')
        search = request.args.get('search')
        
        # Build query
        query = Device.query
        
        if status:
            query = query.filter_by(status=status)
        
        if device_type:
            query = query.filter_by(device_type=device_type)
        
        if search:
            query = query.filter(Device.name.ilike(f'%{search}%'))
        
        # Order by creation date (newest first)
        query = query.order_by(desc(Device.created_at))
        
        # Apply pagination
        devices_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        devices_data = []
        for device in devices_paginated.items:
            device_dict = device.to_dict()
            
            # Add additional metrics
            device_dict['telemetry_count'] = 0  # TODO: Implement InfluxDB telemetry count
            device_dict['is_online'] = (
                device.last_seen and 
                (datetime.now(timezone.utc) - device.last_seen).total_seconds() < 300
            )
            devices_data.append(device_dict)
        
        return jsonify({
            'status': 'success',
            'devices': devices_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': devices_paginated.total,
                'pages': devices_paginated.pages,
                'has_next': devices_paginated.has_next,
                'has_prev': devices_paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error listing devices: {str(e)}")
        return jsonify({
            'error': 'Device listing failed',
            'message': 'An error occurred while retrieving devices'
        }), 500

@admin_bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device_details(device_id):
    """Get detailed information about a specific device"""
    try:
        device = Device.query.get_or_404(device_id)
        
        # Note: Telemetry statistics would need to be retrieved from InfluxDB
        # For now, we'll provide device metadata only
        
        device_data = device.to_dict()
        device_data['statistics'] = {
            'total_telemetry_records': 0,  # TODO: Implement InfluxDB query
            'latest_telemetry': None,      # TODO: Implement InfluxDB query
            'first_telemetry': None,       # TODO: Implement InfluxDB query
            'is_online': (
                device.last_seen and 
                (datetime.now(timezone.utc) - device.last_seen).total_seconds() < 300
            )
        }
        device_data['recent_telemetry'] = []  # TODO: Implement InfluxDB query for recent telemetry
        
        return jsonify({
            'status': 'success',
            'device': device_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting device details: {str(e)}")
        return jsonify({
            'error': 'Device retrieval failed',
            'message': 'An error occurred while retrieving device details'
        }), 500

@admin_bp.route('/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """Update device information (admin only)"""
    try:
        device = Device.query.get_or_404(device_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid JSON',
                'message': 'Request body must contain valid JSON'
            }), 400
        
        # Update allowed fields
        updatable_fields = ['name', 'description', 'status', 'location', 'firmware_version', 'hardware_version']
        
        for field in updatable_fields:
            if field in data:
                setattr(device, field, data[field])
        
        device.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        current_app.logger.info(f"Device updated by admin: {device.name} (ID: {device.id})")
        
        return jsonify({
            'message': 'Device updated successfully',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating device: {str(e)}")
        return jsonify({
            'error': 'Device update failed',
            'message': 'An error occurred while updating the device'
        }), 500

@admin_bp.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a device and all its data"""
    try:
        device = Device.query.get_or_404(device_id)
        device_name = device.name
        
        # Delete device (cascade will handle related records)
        db.session.delete(device)
        db.session.commit()
        
        current_app.logger.warning(f"Device deleted by admin: {device_name} (ID: {device_id})")
        
        return jsonify({
            'message': f'Device {device_name} deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting device: {str(e)}")
        return jsonify({
            'error': 'Device deletion failed',
            'message': 'An error occurred while deleting the device'
        }), 500

@admin_bp.route('/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Device statistics
        total_devices = Device.query.count()
        active_devices = Device.query.filter_by(status='active').count()
        inactive_devices = Device.query.filter_by(status='inactive').count()
        
        # Online devices (seen in last 5 minutes)
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        online_devices = Device.query.filter(Device.last_seen >= five_minutes_ago).count()
        
        # Telemetry statistics - TODO: Implement InfluxDB queries
        total_telemetry = 0
        recent_telemetry = 0
        
        # Device types distribution
        device_types = db.session.query(
            Device.device_type,
            func.count(Device.id).label('count')
        ).group_by(Device.device_type).all()
        
        return jsonify({
            'status': 'success',
            'statistics': {
                'devices': {
                    'total': total_devices,
                    'active': active_devices,
                    'inactive': inactive_devices,
                    'online': online_devices
                },
                'telemetry': {
                    'total_records': total_telemetry,
                    'last_24h': recent_telemetry
                },
                'device_types': [{'type': dt.device_type, 'count': dt.count} for dt in device_types]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({
            'error': 'Dashboard statistics failed',
            'message': 'An error occurred while retrieving dashboard statistics'
        }), 500

@admin_bp.route('/telemetry', methods=['GET'])
def get_all_telemetry():
    """Get telemetry data across all devices"""
    try:
        # Since telemetry is now stored in InfluxDB, this endpoint needs to be reimplemented
        # using InfluxDB queries instead of SQLite
        return jsonify({
            'status': 'success',
            'message': 'Telemetry data is now stored in InfluxDB. Use the telemetry service endpoints instead.',
            'telemetry': [],
            'pagination': {
                'page': 1,
                'per_page': 0,
                'total': 0,
                'pages': 0,
                'has_next': False,
                'has_prev': False
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting telemetry data: {str(e)}")
        return jsonify({
            'error': 'Telemetry retrieval failed',
            'message': 'An error occurred while retrieving telemetry data'
        }), 500
