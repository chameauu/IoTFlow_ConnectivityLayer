#!/usr/bin/env python3
"""
Specialized IoT Device Simulators
Different types of IoT devices with specific behaviors
"""

import requests
import json
import time
import random
import math
from datetime import datetime, timedelta
from basic_device_simulator import BasicIoTDevice

class TemperatureSensor(BasicIoTDevice):
    """Temperature sensor with realistic temperature patterns"""
    
    def __init__(self, device_name, location="Indoor", base_url="http://localhost:5000"):
        super().__init__(device_name, "temperature_sensor", base_url)
        self.location = location
        self.baseline_temp = random.uniform(20, 24)  # Personal baseline
    
    def generate_telemetry(self):
        """Generate realistic temperature sensor data"""
        hour = datetime.now().hour
        
        # Daily temperature cycle
        if self.location == "Indoor":
            # Indoor: more stable, slight daily variation
            temp_variation = 2 * math.sin((hour - 6) * math.pi / 12)
            temperature = self.baseline_temp + temp_variation + random.uniform(-0.5, 0.5)
        else:
            # Outdoor: larger daily variation
            temp_variation = 8 * math.sin((hour - 6) * math.pi / 12)
            temperature = self.baseline_temp + temp_variation + random.uniform(-2, 2)
        
        # Humidity inversely related to temperature
        humidity = 70 - (temperature - 20) * 1.5 + random.uniform(-5, 5)
        humidity = max(20, min(90, humidity))
        
        return {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 1),
            "location": self.location,
            "sensor_status": "active",
            "battery_level": round(self.battery_level, 1)
        }


class SmartDoorLock(BasicIoTDevice):
    """Smart door lock with status changes and events"""
    
    def __init__(self, device_name, base_url="http://localhost:5000"):
        super().__init__(device_name, "smart_lock", base_url)
        self.is_locked = True
        self.last_access_time = None
        self.access_attempts = 0
    
    def generate_telemetry(self):
        """Generate door lock status and events"""
        # Simulate door activity (more during day hours)
        hour = datetime.now().hour
        activity_probability = 0.1 if 22 <= hour or hour <= 6 else 0.3
        
        if random.random() < activity_probability:
            # Simulate lock/unlock event
            self.is_locked = not self.is_locked
            self.last_access_time = datetime.now()
            self.access_attempts += 1
            event_type = "unlock" if not self.is_locked else "lock"
        else:
            event_type = "status_check"
        
        return {
            "lock_status": "locked" if self.is_locked else "unlocked",
            "last_access": self.last_access_time.isoformat() if self.last_access_time else None,
            "event_type": event_type,
            "access_attempts_today": self.access_attempts,
            "battery_level": round(self.battery_level, 1),
            "signal_strength": random.randint(-70, -30)
        }


class SecurityCamera(BasicIoTDevice):
    """Security camera with motion detection events"""
    
    def __init__(self, device_name, base_url="http://localhost:5000"):
        super().__init__(device_name, "security_camera", base_url)
        self.motion_detected = False
        self.recording = False
        self.storage_used = 0
    
    def generate_telemetry(self):
        """Generate camera status and motion events"""
        # Motion detection probability varies by time
        hour = datetime.now().hour
        if 22 <= hour or hour <= 6:  # Night time - less motion
            motion_probability = 0.05
        elif 7 <= hour <= 9 or 17 <= hour <= 19:  # Peak hours
            motion_probability = 0.3
        else:  # Normal hours
            motion_probability = 0.15
        
        # Detect motion
        self.motion_detected = random.random() < motion_probability
        
        if self.motion_detected:
            self.recording = True
            self.storage_used += random.uniform(0.1, 0.5)  # MB per event
        else:
            self.recording = False
        
        return {
            "motion_detected": self.motion_detected,
            "recording_status": "recording" if self.recording else "standby",
            "storage_used_mb": round(self.storage_used, 2),
            "video_quality": "1080p",
            "infrared_mode": hour < 7 or hour > 19,  # Night vision
            "wifi_signal": random.randint(-60, -30)
        }


class AirQualityMonitor(BasicIoTDevice):
    """Air quality monitor with PM2.5 and CO2 levels"""
    
    def __init__(self, device_name, base_url="http://localhost:5000"):
        super().__init__(device_name, "air_quality", base_url)
        self.baseline_pm25 = random.uniform(10, 25)
        self.baseline_co2 = random.uniform(400, 600)
    
    def generate_telemetry(self):
        """Generate air quality measurements"""
        hour = datetime.now().hour
        
        # PM2.5 varies with traffic patterns and time of day
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            pm25_factor = 1.5
        elif 22 <= hour or hour <= 6:  # Night time - cleaner
            pm25_factor = 0.7
        else:
            pm25_factor = 1.0
        
        pm25 = self.baseline_pm25 * pm25_factor + random.uniform(-5, 5)
        pm25 = max(0, pm25)
        
        # CO2 varies with occupancy and ventilation
        co2_variation = 100 * math.sin((hour - 8) * math.pi / 12)  # Peak mid-day
        co2 = self.baseline_co2 + co2_variation + random.uniform(-50, 50)
        co2 = max(350, co2)
        
        # Air quality index based on PM2.5
        if pm25 <= 12:
            aqi = "Good"
        elif pm25 <= 35:
            aqi = "Moderate"
        elif pm25 <= 55:
            aqi = "Unhealthy for Sensitive"
        else:
            aqi = "Unhealthy"
        
        return {
            "pm25": round(pm25, 1),
            "co2": round(co2, 0),
            "air_quality_index": aqi,
            "temperature": round(22 + random.uniform(-2, 2), 1),
            "humidity": round(50 + random.uniform(-10, 10), 1),
            "fan_speed": "auto"
        }


class SmartThermostat(BasicIoTDevice):
    """Smart thermostat with temperature control and schedules"""
    
    def __init__(self, device_name, base_url="http://localhost:5000"):
        super().__init__(device_name, "thermostat", base_url)
        self.target_temp = 22.0
        self.current_temp = 21.5
        self.mode = "auto"  # heat, cool, auto, off
        self.schedule_enabled = True
    
    def get_scheduled_temperature(self):
        """Get target temperature based on schedule"""
        hour = datetime.now().hour
        
        if self.schedule_enabled:
            if 6 <= hour <= 8:  # Morning
                return 21.0
            elif 9 <= hour <= 17:  # Day (away)
                return 19.0
            elif 18 <= hour <= 22:  # Evening
                return 22.0
            else:  # Night
                return 18.0
        else:
            return self.target_temp
    
    def generate_telemetry(self):
        """Generate thermostat status and temperature control"""
        scheduled_temp = self.get_scheduled_temperature()
        
        # Simulate temperature control
        temp_diff = self.current_temp - scheduled_temp
        
        if temp_diff > 1:
            self.mode = "cool"
            self.current_temp -= 0.2
        elif temp_diff < -1:
            self.mode = "heat"
            self.current_temp += 0.3
        else:
            self.mode = "auto"
            # Gradual drift toward target
            self.current_temp += (scheduled_temp - self.current_temp) * 0.1
        
        # Add environmental influence
        outdoor_temp = 15 + 10 * math.sin((datetime.now().hour - 6) * math.pi / 12)
        self.current_temp += (outdoor_temp - self.current_temp) * 0.02
        
        return {
            "current_temperature": round(self.current_temp, 1),
            "target_temperature": round(scheduled_temp, 1),
            "mode": self.mode,
            "schedule_enabled": self.schedule_enabled,
            "heating_cooling": self.mode in ["heat", "cool"],
            "energy_usage_kwh": round(random.uniform(0.5, 2.0), 2) if self.mode in ["heat", "cool"] else 0.1,
            "outdoor_temperature": round(outdoor_temp, 1)
        }


def main():
    """Demo multiple device types"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Specialized IoT Device Simulators')
    parser.add_argument('--device-type', 
                       choices=['temperature', 'door_lock', 'camera', 'air_quality', 'thermostat'],
                       default='temperature',
                       help='Type of device to simulate')
    parser.add_argument('--name', help='Device name (auto-generated if not provided)')
    parser.add_argument('--duration', type=int, default=300, help='Simulation duration in seconds')
    parser.add_argument('--interval', type=int, default=30, help='Data transmission interval in seconds')
    
    args = parser.parse_args()
    
    # Create device based on type
    if args.device_type == 'temperature':
        device = TemperatureSensor(args.name or f"TempSensor_{random.randint(100, 999)}")
    elif args.device_type == 'door_lock':
        device = SmartDoorLock(args.name or f"DoorLock_{random.randint(100, 999)}")
    elif args.device_type == 'camera':
        device = SecurityCamera(args.name or f"Camera_{random.randint(100, 999)}")
    elif args.device_type == 'air_quality':
        device = AirQualityMonitor(args.name or f"AirMonitor_{random.randint(100, 999)}")
    elif args.device_type == 'thermostat':
        device = SmartThermostat(args.name or f"Thermostat_{random.randint(100, 999)}")
    
    # Override telemetry generation method
    device.generate_basic_telemetry = device.generate_telemetry
    
    print(f"🚀 Starting {args.device_type} simulator: {device.device_name}")
    device.run_simulation(args.duration, args.interval, 120)


if __name__ == "__main__":
    main()
