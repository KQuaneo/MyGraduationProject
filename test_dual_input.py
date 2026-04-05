#!/usr/bin/env python3
"""
Test script for dual input system (Voice + Vision)
"""

import os
import sys
import time

# Add the brain modules to path
sys.path.append('/home/raspberrypi/Desktop/MyGraduationProject/brain/online_agent')

def test_vision_system():
    """Test the vision system components"""
    print("🔍 Testing Vision System...")
    
    try:
        from modules.yolov8_qwen import VisionSystem
        
        print("📷 Initializing vision system...")
        vision = VisionSystem()
        
        # Wait for camera to warm up
        time.sleep(3)
        
        print("🎯 Testing person detection...")
        for i in range(5):
            area = vision.closest_person_area
            center_x = vision.closest_person_center_x
            print(f"   Frame {i+1}: Area={area:.3f}, CenterX={center_x}")
            time.sleep(1)
        
        print("🔍 Testing visual analysis...")
        result = vision.analyze_now("你看到了什么？")
        print(f"   Analysis result: {result}")
        
        print("✅ Vision system test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Vision system test failed: {e}")
        return False

def test_audio_system():
    """Test basic audio functionality"""
    print("🎤 Testing Audio System...")
    
    try:
        import pyaudio
        
        p = pyaudio.PyAudio()
        
        # List available audio devices
        print("Available audio devices:")
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            print(f"   {i}: {dev['name']} (in: {dev['maxInputChannels']}, out: {dev['maxOutputChannels']})")
        
        p.terminate()
        print("✅ Audio system test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        return False

def test_dual_input_integration():
    """Test the integration of voice and vision"""
    print("🔄 Testing Dual Input Integration...")
    
    try:
        # Test that both systems can be imported together
        from modules.yolov8_qwen import VisionSystem
        from vosk import Model
        
        print("📚 Loading models...")
        
        # Initialize vision
        vision = VisionSystem()
        time.sleep(2)
        
        # Test voice model loading
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(os.path.dirname(current_dir), "brain", "online_agent", "model")
        
        if os.path.exists(model_path):
            model = Model(model_path)
            print(f"✅ Voice model loaded from {model_path}")
        else:
            print(f"⚠️ Voice model not found at {model_path}")
        
        print("✅ Dual input integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Dual input integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("🚀 Dual Input System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Audio System", test_audio_system),
        ("Vision System", test_vision_system),
        ("Dual Input Integration", test_dual_input_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Dual input system is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above.")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)