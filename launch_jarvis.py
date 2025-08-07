#!/usr/bin/env python3
"""
Launch JARVIS AI Assistant with full audio and visual feedback
"""

import sys
import time
import signal
import threading
sys.path.append('.')

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n👋 Shutting down JARVIS...")
    sys.exit(0)

def main():
    """Main launcher function"""
    print("🚀 JARVIS AI Assistant - Enhanced with Audio Feedback")
    print("=" * 70)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Import and initialize JARVIS
        from jarvis.jarvis_prototype import JARVISPrototype
        from jarvis.audio.sounds import play_startup, play_shutdown
        
        print("🤖 Initializing JARVIS...")
        jarvis = JARVISPrototype()
        
        print("✅ JARVIS initialized successfully!")
        print("📷 Camera system ready!")
        print("🎤 Voice recognition ready!")  
        print("🗣️ Text-to-speech ready!")
        print("🔊 Audio feedback active!")
        print()
        
        # Play startup sound
        play_startup()
        time.sleep(1)
        
        print("🎙️ Voice Commands Available:")
        print("   - 'Hello JARVIS' - Greeting")
        print("   - 'What time is it?' - Get current time")
        print("   - 'What do you see?' - Camera analysis")
        print("   - 'Take a photo' - Capture image")
        print("   - 'How are you?' - Status check")
        print("   - 'Stop' or 'Quit' - Exit JARVIS")
        print()
        print("🔊 Listen for the audio feedback:")
        print("   - Rising beep = Voice detected")
        print("   - Double beep = Processing speech")
        print("   - Success chord = Command completed")
        print("   - Camera click = Photo taken")
        print()
        print("🎤 JARVIS is now listening...")
        print("=" * 70)
        
        # Start the audio system
        jarvis.start()
        
        # Keep running until interrupted
        try:
            while jarvis.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down JARVIS...")
    except Exception as e:
        print(f"❌ Error starting JARVIS: {e}")
        return False
    finally:
        # Cleanup
        if 'jarvis' in locals():
            jarvis.stop()
        
        # Play shutdown sound
        try:
            play_shutdown()
            time.sleep(1)
        except:
            pass
        
        print("✅ JARVIS shutdown complete. Goodbye!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
