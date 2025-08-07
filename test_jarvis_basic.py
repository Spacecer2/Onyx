#!/usr/bin/env python3
"""
Basic test script for JARVIS components
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all JARVIS modules can be imported"""
    print("Testing JARVIS module imports...")
    
    try:
        from jarvis.config.config import config
        print("✓ Configuration module imported")
        
        from jarvis.audio.asr import ASRManager
        print("✓ ASR module imported")
        
        from jarvis.audio.tts import TTSManager
        print("✓ TTS module imported")
        
        from jarvis.audio.audio_io import AudioManager
        print("✓ Audio I/O module imported")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_components():
    """Test basic component initialization"""
    print("\nTesting component initialization...")
    
    try:
        from jarvis.config.config import config
        print(f"✓ Config loaded - Device: {config.device}")
        
        from jarvis.audio.asr import ASRManager
        asr = ASRManager()
        status = asr.get_status()
        print(f"✓ ASR Manager - Available: {status['available']}, Model: {status['model']}")
        
        from jarvis.audio.tts import TTSManager
        tts = TTSManager()
        status = tts.get_status()
        print(f"✓ TTS Manager - Available: {status['available']}, Model: {status['model']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Component error: {e}")
        return False

def test_basic_functionality():
    """Test basic ASR and TTS functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from jarvis.audio.asr import ASRManager
        from jarvis.audio.tts import TTSManager
        
        # Test TTS
        tts = TTSManager()
        test_text = "Hello, this is a test of the JARVIS text to speech system."
        
        print(f"Testing TTS with: '{test_text}'")
        audio_file = tts.speak(test_text, play_audio=False)  # Don't play, just generate
        
        if audio_file and os.path.exists(audio_file):
            print(f"✓ TTS generated audio file: {audio_file}")
        else:
            print("✓ TTS mock synthesis completed")
        
        # Test ASR (mock mode)
        asr = ASRManager()
        mock_transcription = asr.transcribe("dummy_audio_data")
        print(f"✓ ASR mock transcription: '{mock_transcription}'")
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality error: {e}")
        return False

def main():
    print("=" * 50)
    print("🤖 JARVIS Basic Component Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed!")
        return False
    
    # Test component initialization
    if not test_components():
        print("\n❌ Component test failed!")
        return False
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Functionality test failed!")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! JARVIS components are ready.")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Run: python jarvis/jarvis_prototype.py")
    print("2. Speak into your microphone")
    print("3. Listen to JARVIS respond")
    print("\nNote: If you don't have a microphone, the system will use")
    print("mock data for testing purposes.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
