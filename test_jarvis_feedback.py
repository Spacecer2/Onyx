#!/usr/bin/env python3
"""
Test JARVIS with comprehensive audio and visual feedback
"""

import sys
import time
import threading
sys.path.append('.')

def test_sound_feedback():
    """Test all sound feedback types"""
    print("🔊 Testing Sound Feedback System")
    print("=" * 50)
    
    try:
        from jarvis.audio.sounds import (
            play_startup, play_shutdown, play_listening_start, 
            play_listening_stop, play_processing, play_success, 
            play_error, play_camera_click, play_voice_detected, play_thinking
        )
        
        sounds = [
            ("Startup", play_startup),
            ("Voice Detected", play_voice_detected),
            ("Listening Start", play_listening_start),
            ("Processing", play_processing),
            ("Thinking", play_thinking),
            ("Success", play_success),
            ("Camera Click", play_camera_click),
            ("Listening Stop", play_listening_stop),
            ("Error", play_error),
            ("Shutdown", play_shutdown)
        ]
        
        for name, sound_func in sounds:
            print(f"🔊 Playing: {name}")
            sound_func()
            time.sleep(1.5)  # Wait between sounds
        
        print("✅ Sound feedback test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Sound feedback test failed: {e}")
        return False

def test_jarvis_initialization():
    """Test JARVIS initialization with feedback"""
    print("\n🤖 Testing JARVIS Initialization")
    print("=" * 50)
    
    try:
        from jarvis.jarvis_prototype import JARVISPrototype
        
        print("📦 Creating JARVIS instance...")
        jarvis = JARVISPrototype()
        
        print("✅ JARVIS initialized successfully!")
        
        # Test status
        print("\n📊 System Status:")
        status = jarvis._get_system_status()
        print(f"   {status}")
        
        return jarvis
        
    except Exception as e:
        print(f"❌ JARVIS initialization failed: {e}")
        return None

def test_command_processing(jarvis):
    """Test command processing with feedback"""
    print("\n🗣️ Testing Command Processing")
    print("=" * 50)
    
    test_commands = [
        "hello jarvis",
        "hi there", 
        "what time is it",
        "how are you",
        "what do you see",
        "take a photo",
        "unknown command test"
    ]
    
    for cmd in test_commands:
        print(f"\n💬 Testing command: '{cmd}'")
        try:
            response = jarvis._process_command(cmd)
            if response:
                print(f"✅ Response: '{response}'")
            else:
                print("❌ No response generated")
        except Exception as e:
            print(f"❌ Command processing error: {e}")

def main():
    """Main test function"""
    print("🧪 JARVIS Comprehensive Feedback Test")
    print("=" * 60)
    
    # Test 1: Sound Feedback
    if not test_sound_feedback():
        print("⚠️ Sound feedback issues detected")
    
    # Test 2: JARVIS Initialization  
    jarvis = test_jarvis_initialization()
    if not jarvis:
        print("❌ Cannot continue without JARVIS instance")
        return False
    
    # Test 3: Command Processing
    test_command_processing(jarvis)
    
    # Test 4: Interactive Mode
    print("\n🎤 Interactive Test Mode")
    print("=" * 50)
    print("🎙️ JARVIS is ready for voice commands!")
    print("💡 Try saying:")
    print("   - 'Hello JARVIS'")
    print("   - 'What time is it?'") 
    print("   - 'What do you see?'")
    print("   - 'Take a photo'")
    print("🛑 Press Ctrl+C to exit")
    print("=" * 50)
    
    try:
        # Start JARVIS in a separate thread so we can monitor
        jarvis_thread = threading.Thread(target=jarvis.run, daemon=True)
        jarvis_thread.start()
        
        # Monitor for a while
        start_time = time.time()
        while time.time() - start_time < 300:  # Run for 5 minutes max
            time.sleep(1)
            
            # Check if JARVIS is still running
            if not jarvis.running:
                print("🛑 JARVIS stopped")
                break
                
    except KeyboardInterrupt:
        print("\n👋 Stopping JARVIS...")
        jarvis.stop()
        time.sleep(2)  # Wait for shutdown sound
    
    print("✅ Test complete!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal test error: {e}")
        sys.exit(1)
