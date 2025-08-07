#!/usr/bin/env python3
"""
Simple audio test to diagnose issues
"""

import sys
import os
import numpy as np
import time

def test_pyaudio():
    """Test basic PyAudio functionality"""
    print("Testing PyAudio...")
    try:
        import pyaudio
        
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        
        # List audio devices
        print(f"Audio devices found: {audio.get_device_count()}")
        
        # Find default input device
        try:
            default_input = audio.get_default_input_device_info()
            print(f"Default input device: {default_input['name']}")
            print(f"Max input channels: {default_input['maxInputChannels']}")
        except Exception as e:
            print(f"No default input device: {e}")
            return False
        
        # Try to open a stream
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            print("✓ Audio stream opened successfully")
            
            # Test recording for 1 second
            print("Recording 1 second of audio...")
            frames = []
            for i in range(0, int(16000 / 1024)):
                data = stream.read(1024)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Convert to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            print(f"✓ Recorded audio RMS level: {rms:.4f}")
            
            if rms > 100:  # Some reasonable threshold
                print("✓ Audio input appears to be working")
                return True
            else:
                print("⚠ Audio input very quiet - check microphone")
                return True  # Still working, just quiet
                
        except Exception as e:
            print(f"✗ Failed to open audio stream: {e}")
            return False
        
        finally:
            audio.terminate()
            
    except ImportError:
        print("✗ PyAudio not available")
        return False

def test_nemo_asr():
    """Test NeMo ASR with a simple audio file"""
    print("\nTesting NeMo ASR...")
    try:
        sys.path.append('.')
        from jarvis.audio.asr import ASRManager
        
        asr = ASRManager()
        
        # Create a simple test audio file (sine wave)
        sample_rate = 16000
        duration = 2.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = (0.3 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
        
        # Test transcription
        result = asr.transcribe(audio_data)
        print(f"ASR result: '{result}'")
        
        if result:
            print("✓ ASR is working (even if result is not meaningful)")
            return True
        else:
            print("⚠ ASR returned empty result")
            return False
            
    except Exception as e:
        print(f"✗ NeMo ASR test failed: {e}")
        return False

def test_nemo_tts():
    """Test NeMo TTS"""
    print("\nTesting NeMo TTS...")
    try:
        sys.path.append('.')
        from jarvis.audio.tts import TTSManager
        
        tts = TTSManager()
        
        # Test synthesis
        test_text = "This is a test of the text to speech system."
        audio_file = tts.speak(test_text, play_audio=False)
        
        if audio_file and os.path.exists(audio_file):
            print(f"✓ TTS generated audio file: {audio_file}")
            
            # Check file size
            size = os.path.getsize(audio_file)
            print(f"Audio file size: {size} bytes")
            
            if size > 1000:  # Reasonable minimum size
                print("✓ TTS appears to be working")
                return True
            else:
                print("⚠ TTS file very small")
                return False
        else:
            print("✗ TTS failed to generate audio file")
            return False
            
    except Exception as e:
        print(f"✗ NeMo TTS test failed: {e}")
        return False

def test_simple_pipeline():
    """Test a simple text -> TTS -> ASR pipeline"""
    print("\nTesting simple pipeline...")
    try:
        sys.path.append('.')
        from jarvis.audio.tts import TTSManager
        from jarvis.audio.asr import ASRManager
        import soundfile as sf
        
        # Generate speech
        tts = TTSManager()
        test_text = "Hello world"
        audio_file = tts.speak(test_text, play_audio=False)
        
        if not audio_file or not os.path.exists(audio_file):
            print("✗ TTS failed")
            return False
        
        # Try to transcribe it back
        asr = ASRManager()
        result = asr.transcribe(audio_file)
        
        print(f"Original text: '{test_text}'")
        print(f"ASR result: '{result}'")
        
        if result and len(result.strip()) > 0:
            print("✓ Pipeline working (TTS -> ASR)")
            return True
        else:
            print("⚠ Pipeline incomplete - ASR didn't transcribe TTS output")
            return False
            
    except Exception as e:
        print(f"✗ Pipeline test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 JARVIS Audio System Diagnostics")
    print("=" * 60)
    
    results = []
    
    # Test PyAudio
    results.append(("PyAudio", test_pyaudio()))
    
    # Test NeMo ASR
    results.append(("NeMo ASR", test_nemo_asr()))
    
    # Test NeMo TTS
    results.append(("NeMo TTS", test_nemo_tts()))
    
    # Test pipeline
    results.append(("TTS->ASR Pipeline", test_simple_pipeline()))
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC RESULTS")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! The issue might be with voice activity detection.")
        print("\nRecommendations:")
        print("1. Check microphone permissions")
        print("2. Adjust voice activity detection threshold")
        print("3. Test with louder/clearer speech")
    else:
        print("\n🔧 Some tests failed. Issues found:")
        for test_name, passed in results:
            if not passed:
                print(f"- {test_name}")
    
    return all_passed

if __name__ == "__main__":
    main()
