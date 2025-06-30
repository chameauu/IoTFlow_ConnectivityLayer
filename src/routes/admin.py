from flask import Blueprint, request, jsonify, current_app
from src.models import Device, TelemetryData, db
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
            device_dict['telemetry_count'] = TelemetryData.query.filter_by(device_id=device.id).count()
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
        
        # Get telemetry statistics
        telemetry_stats = db.session.query(
            func.count(TelemetryData.id).label('total_records'),
            func.max(TelemetryData.timestamp).label('latest_telemetry'),
            func.min(TelemetryData.timestamp).label('first_telemetry')
        ).filter_by(device_id=device.id).first()
        
        # Get recent telemetry (last 10 records)
        recent_telemetry = TelemetryData.query.filter_by(device_id=device.id)\
            .order_by(desc(TelemetryData.timestamp))\
            .limit(10).all()
        
        device_data = device.to_dict()
        device_data['statistics'] = {
            'total_telemetry_records': telemetry_stats.total_records or 0,
            'latest_telemetry': telemetry_stats.latest_telemetry.isoformat() if telemetry_stats.latest_telemetry else None,
            'first_telemetry': telemetry_stats.first_telemetry.isoformat() if telemetry_stats.first_telemetry else None,
            'is_online': (
                device.last_seen and 
                (datetime.now(timezone.utc) - device.last_seen).total_seconds() < 300
            )
        }
        device_data['recent_telemetry'] = [t.to_dict() for t in recent_telemetry]
        
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
        
        # Telemetry statistics
        total_telemetry = TelemetryData.query.count()
        
        # Recent telemetry (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_telemetry = TelemetryData.query.filter(TelemetryData.timestamp >= yesterday).count()
        
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
        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 100)), 500)
        device_id = request.args.get('device_id')
        data_type = request.args.get('type')
        hours = request.args.get('hours', type=int)
        
        # Build query
        query = TelemetryData.query
        
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        if data_type:
            query = query.filter_by(data_type=data_type)
        
        if hours:
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = query.filter(TelemetryData.timestamp >= time_threshold)
        
        # Join with devices to include device names
        query = query.join(Device).add_columns(Device.name.label('device_name'))
        
        # Order by timestamp descending
        query = query.order_by(desc(TelemetryData.timestamp))
        
        # Apply pagination
        telemetry_paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        telemetry_data = []
        for item in telemetry_paginated.items:
            telemetry_record = item[0]  # TelemetryData object
            device_name = item[1]       # Device name
            
            record_dict = telemetry_record.to_dict()
            record_dict['device_name'] = device_name
            telemetry_data.append(record_dict)
        
        return jsonify({
            'status': 'success',
            'telemetry': telemetry_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': telemetry_paginated.total,
                'pages': telemetry_paginated.pages,
                'has_next': telemetry_paginated.has_next,
                'has_prev': telemetry_paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting telemetry data: {str(e)}")
        return jsonify({
            'error': 'Telemetry retrieval failed',
            'message': 'An error occurred while retrieving telemetry data'
        }), 500
