#!/usr/bin/env python3
"""
Simple JARVIS launcher with minimal dependencies
"""

import os
import sys
import time
import threading
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test all required imports"""
    print("🧪 Testing imports...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import nemo
        print(f"✅ NeMo: {nemo.__version__}")
    except ImportError as e:
        print(f"❌ NeMo import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera access"""
    print("\n📷 Testing camera...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Camera not accessible")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot capture frame")
            cap.release()
            return False
        
        print(f"✅ Camera working: {frame.shape}")
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_audio():
    """Test audio system"""
    print("\n🎤 Testing audio...")
    
    try:
        import pyaudio
        
        p = pyaudio.PyAudio()
        
        # List audio devices
        device_count = p.get_device_count()
        print(f"✅ Found {device_count} audio devices")
        
        # Test default input device
        default_input = p.get_default_input_device_info()
        print(f"✅ Default input: {default_input['name']}")
        
        p.terminate()
        return True
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

class SimpleJARVIS:
    """Simplified JARVIS for testing"""
    
    def __init__(self):
        self.running = False
        print("🤖 Simple JARVIS initializing...")
    
    def start(self):
        """Start simple JARVIS"""
        print("\n" + "="*60)
        print("🤖 SIMPLE JARVIS - READY FOR TESTING")
        print("="*60)
        print("🎤 Voice commands available:")
        print("   - Say anything to test speech recognition")
        print("   - Press Ctrl+C to exit")
        print("="*60)
        
        self.running = True
        
        try:
            # Simple loop to keep running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down Simple JARVIS...")
            self.running = False

def main():
    """Main function"""
    print("🚀 JARVIS System Diagnostics")
    print("="*50)
    
    # Test all components
    if not test_imports():
        print("\n❌ Import tests failed. Please check your environment.")
        return False
    
    if not test_camera():
        print("\n⚠️ Camera test failed. Camera features may not work.")
    
    if not test_audio():
        print("\n⚠️ Audio test failed. Voice features may not work.")
    
    print("\n✅ Basic system tests completed!")
    
    # Ask user if they want to start simple JARVIS
    try:
        response = input("\n🤖 Start Simple JARVIS? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            jarvis = SimpleJARVIS()
            jarvis.start()
        else:
            print("👋 Goodbye!")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
