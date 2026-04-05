#!/usr/bin/env python3
"""
Audio troubleshooting script for VTuber
"""

import os
import sys
import subprocess
import asyncio

# Add the VTuber to path
sys.path.append('/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber')

def check_audio_system():
    """Check the audio system configuration"""
    print("🔍 Checking Audio System...")
    print("=" * 50)
    
    # Check if ALSA is working
    try:
        result = subprocess.run(['speaker-test', '-t', 'wav', '-c', '2', '-l', '1'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ ALSA audio system is working")
        else:
            print("❌ ALSA audio system has issues")
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"❌ ALSA test failed: {e}")
    
    # Check volume levels
    try:
        result = subprocess.run(['amixer', 'sget', 'Master'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📊 Current Volume Levels:")
            for line in result.stdout.split('\n'):
                if 'Playback' in line and '%' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ Could not get volume levels")
    except Exception as e:
        print(f"❌ Volume check failed: {e}")
    
    # List audio devices
    try:
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n🎵 Available Audio Devices:")
            print(result.stdout)
        else:
            print("❌ Could not list audio devices")
    except Exception as e:
        print(f"❌ Audio device listing failed: {e}")

def test_edge_tts():
    """Test Edge TTS functionality"""
    print("\n🔤 Testing Edge TTS...")
    print("=" * 50)
    
    try:
        import edge_tts
        print("✅ Edge TTS library is available")
        
        async def test_tts_generation():
            try:
                communicate = edge_tts.Communicate("Hello, this is a test of the text to speech system.", 
                                                 voice="zh-CN-XiaoxiaoNeural")
                await communicate.save("/tmp/test_tts.mp3")
                return True
            except Exception as e:
                print(f"❌ TTS generation failed: {e}")
                return False
        
        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(test_tts_generation())
        loop.close()
        
        if success:
            print("✅ TTS audio file generated successfully")
            
            # Check if file exists and has content
            if os.path.exists("/tmp/test_tts.mp3"):
                file_size = os.path.getsize("/tmp/test_tts.mp3")
                print(f"✅ Audio file size: {file_size} bytes")
                
                # Try to play the file
                try:
                    result = subprocess.run(['mpg123', '/tmp/test_tts.mp3'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print("✅ Audio playback successful")
                    else:
                        print("❌ Audio playback failed")
                        print("STDERR:", result.stderr)
                except Exception as e:
                    print(f"❌ Playback test failed: {e}")
            else:
                print("❌ Audio file was not created")
        
    except ImportError:
        print("❌ Edge TTS library not available")
    except Exception as e:
        print(f"❌ Edge TTS test failed: {e}")

def check_vtuber_audio_config():
    """Check VTuber audio configuration"""
    print("\n⚙️  Checking VTuber Audio Configuration...")
    print("=" * 50)
    
    config_path = "/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/conf.yaml"
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Check TTS configuration
        if 'tts_config' in config:
            tts_config = config['tts_config']
            print("📝 TTS Configuration:")
            print(f"   Module: {tts_config.get('tts_module', 'Not set')}")
            print(f"   Voice: {tts_config.get('edge_tts', {}).get('voice', 'Not set')}")
            print(f"   Rate: {tts_config.get('edge_tts', {}).get('rate', 'Not set')}")
            print(f"   Volume: {tts_config.get('edge_tts', {}).get('volume', 'Not set')}")
        else:
            print("❌ No TTS configuration found")
        
        # Check ASR configuration
        if 'asr_config' in config:
            asr_config = config['asr_config']
            print(f"\n🎤 ASR Configuration:")
            print(f"   Module: {asr_config.get('asr_module', 'Not set')}")
            print(f"   Language: {asr_config.get('sherpa_onnx', {}).get('language', 'Not set')}")
        else:
            print("❌ No ASR configuration found")
            
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")

def test_virtual_environment():
    """Test if virtual environment has required packages"""
    print("\n🔧 Checking Virtual Environment...")
    print("=" * 50)
    
    venv_python = "/home/raspberrypi/Desktop/MyGraduationProject/Open-LLM-VTuber/.venv/bin/python"
    
    if not os.path.exists(venv_python):
        print("❌ Virtual environment Python not found!")
        return
    
    try:
        # Test importing audio-related packages
        packages = ['edge_tts', 'pyaudio', 'numpy', 'sounddevice']
        
        for package in packages:
            try:
                result = subprocess.run([venv_python, '-c', f'import {package}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {package} is available")
                else:
                    print(f"❌ {package} import failed: {result.stderr}")
            except Exception as e:
                print(f"❌ {package} check failed: {e}")
                
    except Exception as e:
        print(f"❌ Virtual environment check failed: {e}")

def main():
    """Run all audio troubleshooting tests"""
    print("🔊 VTuber Audio Troubleshooting")
    print("=" * 60)
    
    check_audio_system()
    test_virtual_environment()
    test_edge_tts()
    check_vtuber_audio_config()
    
    print("\n" + "=" * 60)
    print("📋 Troubleshooting Summary:")
    print("1. Check if ALSA audio system is working")
    print("2. Verify Edge TTS can generate audio files")
    print("3. Test if generated audio can be played")
    print("4. Check VTuber configuration")
    print("\n💡 Next steps:")
    print("- If ALSA fails: Check audio hardware and drivers")
    print("- If TTS fails: Check internet connection and API")
    print("- If playback fails: Check volume and audio output device")
    print("- If config issues: Update conf.yaml with correct settings")
    print("=" * 60)

if __name__ == "__main__":
    main()