#!/usr/bin/env python3
"""
Test camera functionality for JARVIS
"""

import sys
import time
sys.path.append('.')

from jarvis.vision.camera import VisionManager
from jarvis.vision.analysis import VisionAnalysisManager

def test_camera():
    print("🧪 Testing JARVIS Camera System")
    print("=" * 50)
    
    # Initialize vision system
    vision_manager = VisionManager()
    vision_analyzer = VisionAnalysisManager()
    
    try:
        # Start camera
        print("📷 Starting camera...")
        if not vision_manager.start_vision_system():
            print("❌ Failed to start camera system")
            return False
        
        print("✅ Camera system started!")
        
        # Wait a moment for camera to stabilize
        print("⏳ Waiting for camera to stabilize...")
        time.sleep(2)
        
        # Get camera status
        status = vision_manager.get_vision_status()
        print(f"📊 Camera Status:")
        print(f"   - Active: {status['vision_active']}")
        print(f"   - Resolution: {status['camera']['actual_resolution']}")
        print(f"   - FPS: {status['camera']['actual_fps']}")
        print(f"   - Backend: {status['camera']['backend']}")
        
        # Test photo capture
        print("\n📸 Testing photo capture...")
        photo_path = vision_manager.take_photo("Test photo")
        
        if photo_path:
            print(f"✅ Photo saved: {photo_path}")
        else:
            print("❌ Failed to take photo")
        
        # Test vision analysis
        print("\n🧠 Testing vision analysis...")
        frame = vision_manager.camera.get_current_frame()
        
        if frame is not None:
            description = vision_analyzer.analyze_current_view(frame)
            print(f"👁️ What I see: {description}")
        else:
            print("❌ No frame available for analysis")
        
        # Keep camera running for a few seconds
        print("\n⏱️ Camera running for 5 seconds...")
        for i in range(5, 0, -1):
            print(f"   {i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during camera test: {e}")
        return False
        
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        vision_manager.stop_vision_system()
        print("✅ Camera test complete!")

if __name__ == "__main__":
    success = test_camera()
    sys.exit(0 if success else 1)
