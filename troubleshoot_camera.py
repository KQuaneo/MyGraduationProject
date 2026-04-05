#!/usr/bin/env python3
"""
Camera troubleshooting script for VTuber
"""

import os
import sys
import subprocess
import cv2

def check_pi_camera():
    """Check if Pi camera is available and enabled"""
    print("🔍 Checking Pi Camera...")
    print("=" * 50)
    
    # Check if camera is detected
    try:
        result = subprocess.run(['vcgencmd', 'get_camera'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📷 Camera Detection Status:")
            print(result.stdout)
            
            if 'detected=1' in result.stdout:
                print("✅ Pi camera is detected")
            else:
                print("❌ Pi camera not detected")
        else:
            print("❌ Could not check camera status")
    except Exception as e:
        print(f"❌ Camera detection failed: {e}")
    
    # Check if camera module is enabled
    try:
        if os.path.exists('/boot/config.txt'):
            with open('/boot/config.txt', 'r') as f:
                content = f.read()
                if 'start_x=1' in content:
                    print("✅ Camera module is enabled in config.txt")
                else:
                    print("❌ Camera module not enabled - add 'start_x=1' to /boot/config.txt")
                
                if 'gpu_mem=128' in content:
                    print("✅ GPU memory is sufficient")
                else:
                    print("⚠️  Consider adding 'gpu_mem=128' to /boot/config.txt")
        else:
            print("❌ /boot/config.txt not found")
    except Exception as e:
        print(f"❌ Config file check failed: {e}")

def check_usb_cameras():
    """Check for USB webcams"""
    print("\n🔌 Checking USB Cameras...")
    print("=" * 50)
    
    # List video devices
    try:
        result = subprocess.run(['ls', '/dev/video*'], capture_output=True, text=True)
        if result.returncode == 0:
            devices = result.stdout.strip().split('\n')
            print(f"📹 Found {len(devices)} video devices:")
            for device in devices:
                print(f"   {device}")
            return devices
        else:
            print("❌ No video devices found")
            return []
    except Exception as e:
        print(f"❌ USB camera check failed: {e}")
        return []

def test_camera_with_opencv():
    """Test camera access with OpenCV"""
    print("\n🧪 Testing Camera with OpenCV...")
    print("=" * 50)
    
    try:
        import cv2
        print("✅ OpenCV is available")
        
        # Test each video device
        for i in range(4):  # Try first 4 video devices
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    print(f"✅ Camera {i} is accessible")
                    
                    # Try to read a frame
                    ret, frame = cap.read()
                    if ret:
                        print(f"✅ Camera {i} can capture frames ({frame.shape[1]}x{frame.shape[0]})")
                        
                        # Save a test image
                        cv2.imwrite(f'/tmp/camera_test_{i}.jpg', frame)
                        print(f"✅ Test image saved as /tmp/camera_test_{i}.jpg")
                    else:
                        print(f"❌ Camera {i} cannot capture frames")
                    
                    cap.release()
                else:
                    print(f"❌ Camera {i} is not accessible")
                    
            except Exception as e:
                print(f"❌ Camera {i} test failed: {e}")
                
    except ImportError:
        print("❌ OpenCV not available")
    except Exception as e:
        print(f"❌ OpenCV test failed: {e}")

def check_browser_camera_access():
    """Check browser camera access setup"""
    print("\n🌐 Checking Browser Camera Access...")
    print("=" * 50)
    
    # Check if running on localhost (required for camera access)
    print("📡 Server Configuration:")
    print("   The VTuber server should be accessible via:")
    print("   - http://localhost:12393 (for development)")
    print("   - HTTPS for production (required for camera access)")
    
    # Create a simple test HTML page
    test_html = """<!DOCTYPE html>
<html>
<head>
    <title>Camera Test</title>
</head>
<body>
    <h2>Camera Test Page</h2>
    <video id="video" width="640" height="480" autoplay></video>
    <br>
    <button onclick="startCamera()">Start Camera</button>
    <button onclick="stopCamera()">Stop Camera</button>
    <div id="status">Camera status will appear here</div>
    
    <script>
        let stream = null;
        
        async function startCamera() {
            try {
                const status = document.getElementById('status');
                status.innerHTML = 'Requesting camera access...';
                
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: true, 
                    audio: false 
                });
                
                const video = document.getElementById('video');
                video.srcObject = stream;
                status.innerHTML = '✅ Camera is working!';
                
            } catch (err) {
                const status = document.getElementById('status');
                status.innerHTML = '❌ Error: ' + err.message;
                console.error('Camera error:', err);
            }
        }
        
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                const video = document.getElementById('video');
                video.srcObject = null;
                const status = document.getElementById('status');
                status.innerHTML = 'Camera stopped';
            }
        }
    </script>
</body>
</html>"""
    
    try:
        with open('/tmp/camera_test.html', 'w') as f:
            f.write(test_html)
        print("✅ Camera test page created: /tmp/camera_test.html")
        print("   Open this file in a browser to test camera access")
    except Exception as e:
        print(f"❌ Could not create test page: {e}")

def check_v4l2():
    """Check v4l2 (Video4Linux) setup"""
    print("\n🎥 Checking V4L2 Setup...")
    print("=" * 50)
    
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📹 V4L2 Devices:")
            print(result.stdout)
        else:
            print("❌ V4L2 not available or no devices")
    except Exception as e:
        print(f"❌ V4L2 check failed: {e}")
    
    try:
        result = subprocess.run(['v4l2-ctl', '--list-formats'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📊 Supported Formats:")
            print(result.stdout)
        else:
            print("❌ Could not get format information")
    except Exception as e:
        print(f"❌ Format check failed: {e}")

def main():
    """Run all camera troubleshooting tests"""
    print("📷 VTuber Camera Troubleshooting")
    print("=" * 60)
    
    check_pi_camera()
    check_usb_cameras()
    check_v4l2()
    test_camera_with_opencv()
    check_browser_camera_access()
    
    print("\n" + "=" * 60)
    print("📋 Camera Troubleshooting Summary:")
    print("1. Check if Pi camera or USB camera is detected")
    print("2. Verify camera module is enabled in /boot/config.txt")
    print("3. Test camera access with OpenCV")
    print("4. Test browser camera access with the generated HTML page")
    print("\n💡 Next steps:")
    print("- If Pi camera not detected: Enable camera module and reboot")
    print("- If USB camera not found: Check connection and drivers")
    print("- If browser camera fails: Ensure HTTPS or localhost access")
    print("- Open /tmp/camera_test.html in browser to test camera")
    print("=" * 60)

if __name__ == "__main__":
    main()