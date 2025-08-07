#!/usr/bin/env python3
"""
Start JARVIS AI Assistant with full capabilities
"""

import sys
import signal
import time
sys.path.append('.')

from jarvis.jarvis_prototype import JARVISAssistant

def main():
    print("🤖 JARVIS AI Assistant - Starting Up...")
    print("=" * 60)
    
    try:
        # Initialize JARVIS
        jarvis = JARVISAssistant()
        
        print("✅ JARVIS initialized successfully!")
        print("📷 Camera system ready!")
        print("🎤 Voice recognition ready!")  
        print("🗣️ Text-to-speech ready!")
        print()
        print("🎙️ Try these voice commands:")
        print("   - 'Hello JARVIS'")
        print("   - 'What do you see?'")
        print("   - 'Take a photo'")
        print("   - 'What time is it?'")
        print("   - 'Stop' to exit")
        print()
        print("🔊 Listening for voice commands...")
        print("=" * 60)
        
        # Start JARVIS
        jarvis.run()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down JARVIS...")
        if 'jarvis' in locals():
            jarvis.stop()
        print("✅ Goodbye!")
    except Exception as e:
        print(f"❌ Error starting JARVIS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
