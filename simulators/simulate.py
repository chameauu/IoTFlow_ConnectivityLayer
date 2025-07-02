#!/usr/bin/env python3
"""
IoT Device Simulation Control Script
Easy-to-use interface for running device simulations
"""

import subprocess
import sys
import time
import requests
import argparse
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_service_health(base_url="http://localhost:5000"):
    """Check if the IoT service is running"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ IoT service is running at {base_url}")
            return True
        else:
            print(f"❌ IoT service responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to IoT service at {base_url}")
        print(f"   Error: {e}")
        print("\n💡 To start the service:")
        print("   1. Start Docker services: ./docker-manage.sh start")
        print("   2. Start Flask app: poetry run python app.py")
        return False

def run_single_device(device_type, name=None, duration=300, interval=30):
    """Run a single device simulator"""
    print(f"\n🚀 Starting single {device_type} device simulation")
    
    if device_type == "basic":
        cmd = [
            "poetry", "run", "python", "simulators/basic_device_simulator.py",
            "--duration", str(duration),
            "--telemetry-interval", str(interval)
        ]
        if name:
            cmd.extend(["--name", name])
    else:
        cmd = [
            "poetry", "run", "python", "simulators/device_types.py",
            "--device-type", device_type,
            "--duration", str(duration),
            "--interval", str(interval)
        ]
        if name:
            cmd.extend(["--name", name])
    
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)  # Run from project root to use Poetry
    except KeyboardInterrupt:
        print("\n🛑 Device simulation stopped")
    except Exception as e:
        print(f"❌ Error running device simulation: {e}")

def run_fleet_simulation(preset="home", duration=600, telemetry_interval=60):
    """Run fleet simulation with preset configuration"""
    print(f"\n🚀 Starting {preset} fleet simulation")
    print(f"   Duration: {duration} seconds ({duration//60} minutes)")
    
    cmd = [
        "poetry", "run", "python", "simulators/fleet_simulator.py",
        "--preset", preset,
        "--duration", str(duration),
        "--telemetry-interval", str(telemetry_interval)
    ]
    
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)  # Run from project root to use Poetry
    except KeyboardInterrupt:
        print("\n🛑 Fleet simulation stopped")
    except Exception as e:
        print(f"❌ Error running fleet simulation: {e}")

def run_custom_fleet(**device_counts):
    """Run custom fleet with specified device counts"""
    print("\n🚀 Starting custom fleet simulation")
    
    cmd = ["poetry", "run", "python", "simulators/fleet_simulator.py", "--preset", "custom"]
    
    for device_type, count in device_counts.items():
        if count > 0:
            cmd.extend([f"--{device_type.replace('_', '-')}", str(count)])
    
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)  # Run from project root to use Poetry
    except KeyboardInterrupt:
        print("\n🛑 Custom fleet simulation stopped")
    except Exception as e:
        print(f"❌ Error running custom fleet simulation: {e}")

def show_menu():
    """Show interactive menu for simulation options"""
    print("\n" + "="*60)
    print("🌐 IoT Device Simulation Control Center")
    print("="*60)
    print("1. Single Device Simulations:")
    print("   a) Basic sensor device")
    print("   b) Temperature sensor")
    print("   c) Smart door lock")
    print("   d) Security camera")
    print("   e) Air quality monitor")
    print("   f) Smart thermostat")
    print()
    print("2. Fleet Simulations:")
    print("   g) Home setup (9 devices)")
    print("   h) Office setup (16 devices)")
    print("   i) Factory setup (30 devices)")
    print("   j) Custom fleet")
    print()
    print("3. System:")
    print("   k) Check service health")
    print("   l) View admin dashboard")
    print("   q) Quit")
    print("="*60)

def open_admin_dashboard():
    """Open admin dashboard in browser"""
    import webbrowser
    dashboard_url = "http://localhost:5000/api/v1/admin/dashboard"
    print(f"🌐 Opening admin dashboard: {dashboard_url}")
    try:
        webbrowser.open(dashboard_url)
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"   Manually visit: {dashboard_url}")

def interactive_mode():
    """Run in interactive mode with menu"""
    while True:
        show_menu()
        choice = input("\nSelect an option: ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == 'k':
            check_service_health()
        elif choice == 'l':
            open_admin_dashboard()
        elif choice == 'a':
            run_single_device("basic", duration=180, interval=20)
        elif choice == 'b':
            run_single_device("temperature", duration=180, interval=30)
        elif choice == 'c':
            run_single_device("door_lock", duration=180, interval=60)
        elif choice == 'd':
            run_single_device("camera", duration=180, interval=45)
        elif choice == 'e':
            run_single_device("air_quality", duration=180, interval=90)
        elif choice == 'f':
            run_single_device("thermostat", duration=180, interval=120)
        elif choice == 'g':
            run_fleet_simulation("home", duration=300, telemetry_interval=60)
        elif choice == 'h':
            run_fleet_simulation("office", duration=300, telemetry_interval=45)
        elif choice == 'i':
            run_fleet_simulation("factory", duration=600, telemetry_interval=30)
        elif choice == 'j':
            print("\n📝 Custom Fleet Configuration:")
            temp_sensors = int(input("Temperature sensors (0-10): ") or "0")
            door_locks = int(input("Smart door locks (0-5): ") or "0")
            cameras = int(input("Security cameras (0-8): ") or "0")
            air_monitors = int(input("Air quality monitors (0-5): ") or "0")
            thermostats = int(input("Smart thermostats (0-3): ") or "0")
            
            run_custom_fleet(
                temperature_sensors=temp_sensors,
                door_locks=door_locks,
                cameras=cameras,
                air_monitors=air_monitors,
                thermostats=thermostats
            )
        else:
            print(f"❌ Invalid option: {choice}")
        
        if choice != 'q':
            input("\nPress Enter to continue...")

def main():
    parser = argparse.ArgumentParser(description='IoT Device Simulation Control')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--check-health', action='store_true',
                       help='Check service health and exit')
    parser.add_argument('--device-type', 
                       choices=['basic', 'temperature', 'door_lock', 'camera', 
                               'air_quality', 'thermostat'],
                       help='Run single device of specified type')
    parser.add_argument('--fleet-preset',
                       choices=['home', 'office', 'factory'],
                       help='Run fleet simulation with preset')
    parser.add_argument('--duration', type=int, default=300,
                       help='Simulation duration in seconds')
    
    args = parser.parse_args()
    
    # Check service health first
    if not check_service_health():
        return 1
    
    if args.check_health:
        return 0
    
    if args.interactive or (not args.device_type and not args.fleet_preset):
        interactive_mode()
    elif args.device_type:
        run_single_device(args.device_type, duration=args.duration)
    elif args.fleet_preset:
        run_fleet_simulation(args.fleet_preset, duration=args.duration)
    
    return 0

if __name__ == "__main__":
    exit(main())
