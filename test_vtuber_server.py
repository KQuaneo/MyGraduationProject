#!/usr/bin/env python3
"""
Test script for Open-LLM-VTuber server
"""

import os
import sys
import time
import subprocess
import signal
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'uvicorn',
        'loguru', 
        'tomli',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_configuration():
    """Check if configuration files exist and are valid"""
    print("🔍 Checking configuration...")
    
    config_path = Path("/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/conf.yaml")
    
    if not config_path.exists():
        print("❌ Configuration file not found!")
        return False
    
    print("✅ Configuration file exists")
    
    # Check if the configuration has required sections
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'system_config' not in config:
            print("❌ Missing system_config section")
            return False
        
        if 'character_config' not in config:
            print("❌ Missing character_config section") 
            return False
            
        print("✅ Configuration structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False

def check_frontend():
    """Check if frontend files exist"""
    print("🔍 Checking frontend...")
    
    frontend_path = Path("/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/frontend")
    
    if not frontend_path.exists():
        print("❌ Frontend directory not found!")
        return False
    
    index_file = frontend_path / "index.html"
    if not index_file.exists():
        print("❌ Frontend index.html not found!")
        return False
    
    print("✅ Frontend files exist")
    return True

def test_server_startup(timeout=30):
    """Test if the server can start successfully"""
    print("🚀 Testing server startup...")
    
    server_path = "/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/run_server.py"
    
    try:
        # Start the server in background
        print("📡 Starting server...")
        process = subprocess.Popen(
            [sys.executable, server_path, "--verbose"],
            cwd="/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for server to start
        print("⏳ Waiting for server to initialize...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if process is still running
            if process.poll() is not None:
                # Process finished, check output
                stdout, stderr = process.communicate()
                print("❌ Server exited prematurely:")
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
                return False
            
            # Try to connect to the server
            try:
                response = requests.get("http://localhost:12393", timeout=2)
                if response.status_code == 200:
                    print("✅ Server is responding successfully!")
                    return True
            except requests.exceptions.RequestException:
                pass  # Server not ready yet
            
            time.sleep(2)
        
        # Timeout reached
        print("❌ Server startup timeout")
        return False
        
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False
    finally:
        # Clean up - terminate the server process
        if 'process' in locals() and process.poll() is None:
            print("🛑 Stopping test server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

def check_logs():
    """Check if logs directory exists and is writable"""
    print("🔍 Checking logs directory...")
    
    logs_path = Path("/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/logs")
    
    try:
        if not logs_path.exists():
            logs_path.mkdir(parents=True)
            print("✅ Created logs directory")
        else:
            print("✅ Logs directory exists")
        
        # Test write permission
        test_file = logs_path / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print("✅ Logs directory is writable")
        return True
        
    except Exception as e:
        print(f"❌ Error with logs directory: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Open-LLM-VTuber Server Test Suite")
    print("=" * 60)
    
    tests = [
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("Frontend", check_frontend),
        ("Logs Directory", check_logs),
        ("Server Startup", test_server_startup)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_name == "Server Startup":
                # Special handling for server test with longer timeout
                result = test_func(timeout=45)
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! VTuber server should work correctly.")
        print("💡 You can start the server with:")
        print("   cd /home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber")
        print("   python run_server.py")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        print("🔧 You may need to fix the issues before the server will work.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)