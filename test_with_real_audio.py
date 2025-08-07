#!/usr/bin/env python3
"""
Test JARVIS components with real audio samples from the internet
"""

import sys
import os
import requests
import numpy as np
import soundfile as sf
import librosa
from pathlib import Path

def download_test_audio():
    """Download test audio samples from various sources"""
    print("📥 Downloading test audio samples...")
    
    # Create test audio directory
    test_dir = Path("test_audio_samples")
    test_dir.mkdir(exist_ok=True)
    
    # List of test audio URLs (public domain or creative commons)
    test_samples = [
        {
            "name": "librispeech_sample",
            "url": "https://www.openslr.org/resources/12/test-clean.tar.gz",
            "description": "LibriSpeech test sample",
            "type": "archive"
        },
        {
            "name": "mozilla_common_voice",
            "url": "https://commonvoice.mozilla.org/api/v1/clips",
            "description": "Mozilla Common Voice sample",
            "type": "api"
        }
    ]
    
    # For simplicity, let's use some direct audio file URLs
    direct_samples = [
        {
            "name": "harvard_sentences_1.wav",
            "url": "https://www2.cs.uic.edu/~i101/SoundFiles/CantinaBand3.wav",
            "description": "Test audio file"
        },
        {
            "name": "speech_sample_1.wav", 
            "url": "https://file-examples.com/storage/fe68c1b7c1a9fd42d95c7bb/2017/11/file_example_WAV_1MG.wav",
            "description": "Speech sample"
        }
    ]
    
    downloaded_files = []
    
    # Try to download some samples
    for sample in direct_samples:
        try:
            print(f"  Downloading {sample['name']}...")
            response = requests.get(sample['url'], timeout=30)
            if response.status_code == 200:
                file_path = test_dir / sample['name']
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                downloaded_files.append(str(file_path))
                print(f"  ✓ Downloaded {sample['name']}")
            else:
                print(f"  ✗ Failed to download {sample['name']}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error downloading {sample['name']}: {e}")
    
    # If downloads fail, create synthetic speech samples
    if not downloaded_files:
        print("  Creating synthetic speech samples...")
        downloaded_files = create_synthetic_samples(test_dir)
    
    return downloaded_files

def create_synthetic_samples(test_dir):
    """Create synthetic audio samples for testing"""
    print("  🔧 Creating synthetic audio samples...")
    
    synthetic_files = []
    
    # Create different types of test signals
    sample_rate = 16000
    duration = 3.0
    
    # 1. Pure tone (should not transcribe to speech)
    t = np.linspace(0, duration, int(sample_rate * duration))
    tone = 0.3 * np.sin(2 * np.pi * 440 * t)  # A4 note
    tone_file = test_dir / "tone_440hz.wav"
    sf.write(tone_file, tone, sample_rate)
    synthetic_files.append(str(tone_file))
    print(f"    ✓ Created {tone_file.name}")
    
    # 2. White noise (should not transcribe to speech)
    noise = 0.1 * np.random.normal(0, 1, int(sample_rate * duration))
    noise_file = test_dir / "white_noise.wav"
    sf.write(noise_file, noise, sample_rate)
    synthetic_files.append(str(noise_file))
    print(f"    ✓ Created {noise_file.name}")
    
    # 3. Chirp signal (frequency sweep)
    chirp = 0.3 * np.sin(2 * np.pi * (100 + (1000-100) * t / duration) * t)
    chirp_file = test_dir / "chirp_signal.wav"
    sf.write(chirp_file, chirp, sample_rate)
    synthetic_files.append(str(chirp_file))
    print(f"    ✓ Created {chirp_file.name}")
    
    # 4. Simulated speech-like signal (formant-like structure)
    # Create a signal with formant-like characteristics
    f1, f2, f3 = 800, 1200, 2400  # Typical formant frequencies for vowel /a/
    speech_like = (0.3 * np.sin(2 * np.pi * f1 * t) + 
                   0.2 * np.sin(2 * np.pi * f2 * t) + 
                   0.1 * np.sin(2 * np.pi * f3 * t))
    # Add some amplitude modulation to simulate speech rhythm
    speech_like *= (1 + 0.5 * np.sin(2 * np.pi * 3 * t))
    speech_file = test_dir / "synthetic_speech.wav"
    sf.write(speech_file, speech_like, sample_rate)
    synthetic_files.append(str(speech_file))
    print(f"    ✓ Created {speech_file.name}")
    
    return synthetic_files

def test_asr_with_files(audio_files):
    """Test ASR with downloaded audio files"""
    print("\n🎤 Testing ASR with real audio files...")
    
    try:
        sys.path.append('.')
        from jarvis.audio.asr import ASRManager
        
        asr = ASRManager()
        results = []
        
        for audio_file in audio_files:
            print(f"\n  Testing: {os.path.basename(audio_file)}")
            
            try:
                # Load audio file
                audio_data, sr = librosa.load(audio_file, sr=16000, mono=True)
                print(f"    Loaded: {len(audio_data)} samples, {len(audio_data)/sr:.2f}s duration")
                
                # Get audio statistics
                rms = np.sqrt(np.mean(audio_data ** 2))
                peak = np.max(np.abs(audio_data))
                print(f"    Audio stats: RMS={rms:.4f}, Peak={peak:.4f}")
                
                # Transcribe
                transcription = asr.transcribe(audio_data)
                print(f"    ASR Result: '{transcription}'")
                
                results.append({
                    'file': os.path.basename(audio_file),
                    'duration': len(audio_data)/sr,
                    'rms': rms,
                    'peak': peak,
                    'transcription': transcription,
                    'success': len(transcription.strip()) > 0
                })
                
            except Exception as e:
                print(f"    ✗ Error processing {audio_file}: {e}")
                results.append({
                    'file': os.path.basename(audio_file),
                    'error': str(e),
                    'success': False
                })
        
        return results
        
    except Exception as e:
        print(f"✗ ASR test failed: {e}")
        return []

def test_tts_quality():
    """Test TTS with various text samples"""
    print("\n🗣️ Testing TTS with various text samples...")
    
    try:
        sys.path.append('.')
        from jarvis.audio.tts import TTSManager
        
        tts = TTSManager()
        
        # Test phrases of varying complexity
        test_phrases = [
            "Hello world",
            "The quick brown fox jumps over the lazy dog",
            "JARVIS is an artificial intelligence assistant",
            "Testing one two three four five",
            "How are you doing today?",
            "This is a longer sentence with multiple clauses, punctuation, and various words to test the text-to-speech synthesis quality.",
            "Numbers: one, two, three, 123, 456",
            "Special characters: Hello! How are you? That's great.",
        ]
        
        results = []
        
        for i, phrase in enumerate(test_phrases):
            print(f"\n  Testing phrase {i+1}: '{phrase[:50]}{'...' if len(phrase) > 50 else ''}'")
            
            try:
                # Generate speech
                audio_file = tts.speak(phrase, play_audio=False)
                
                if audio_file and os.path.exists(audio_file):
                    # Analyze generated audio
                    audio_data, sr = librosa.load(audio_file, sr=None)
                    duration = len(audio_data) / sr
                    rms = np.sqrt(np.mean(audio_data ** 2))
                    
                    print(f"    ✓ Generated: {duration:.2f}s, RMS={rms:.4f}")
                    
                    results.append({
                        'phrase': phrase,
                        'file': audio_file,
                        'duration': duration,
                        'rms': rms,
                        'success': True
                    })
                else:
                    print(f"    ✗ Failed to generate audio")
                    results.append({
                        'phrase': phrase,
                        'success': False
                    })
                    
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results.append({
                    'phrase': phrase,
                    'error': str(e),
                    'success': False
                })
        
        return results
        
    except Exception as e:
        print(f"✗ TTS test failed: {e}")
        return []

def test_round_trip():
    """Test TTS -> ASR round trip"""
    print("\n🔄 Testing TTS -> ASR round trip...")
    
    try:
        sys.path.append('.')
        from jarvis.audio.tts import TTSManager
        from jarvis.audio.asr import ASRManager
        
        tts = TTSManager()
        asr = ASRManager()
        
        test_phrases = [
            "Hello JARVIS",
            "What time is it",
            "How are you today",
            "Testing speech recognition",
            "The weather is nice"
        ]
        
        results = []
        
        for phrase in test_phrases:
            print(f"\n  Testing: '{phrase}'")
            
            try:
                # Generate speech
                audio_file = tts.speak(phrase, play_audio=False)
                
                if audio_file and os.path.exists(audio_file):
                    # Transcribe it back
                    transcription = asr.transcribe(audio_file)
                    
                    # Calculate similarity (simple word overlap)
                    original_words = set(phrase.lower().split())
                    transcribed_words = set(transcription.lower().split())
                    
                    if original_words and transcribed_words:
                        overlap = len(original_words & transcribed_words)
                        similarity = overlap / len(original_words)
                    else:
                        similarity = 0.0
                    
                    print(f"    Original:    '{phrase}'")
                    print(f"    Transcribed: '{transcription}'")
                    print(f"    Similarity:  {similarity:.2%}")
                    
                    results.append({
                        'original': phrase,
                        'transcribed': transcription,
                        'similarity': similarity,
                        'success': len(transcription.strip()) > 0
                    })
                else:
                    print(f"    ✗ TTS failed")
                    results.append({
                        'original': phrase,
                        'success': False,
                        'error': 'TTS failed'
                    })
                    
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results.append({
                    'original': phrase,
                    'error': str(e),
                    'success': False
                })
        
        return results
        
    except Exception as e:
        print(f"✗ Round trip test failed: {e}")
        return []

def main():
    print("=" * 80)
    print("🧪 JARVIS Real Audio Testing Suite")
    print("=" * 80)
    
    # Download test audio
    audio_files = download_test_audio()
    
    # Test ASR with real audio
    asr_results = test_asr_with_files(audio_files)
    
    # Test TTS quality
    tts_results = test_tts_quality()
    
    # Test round trip
    roundtrip_results = test_round_trip()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n🎤 ASR Results:")
    asr_success = sum(1 for r in asr_results if r.get('success', False))
    print(f"  Successful transcriptions: {asr_success}/{len(asr_results)}")
    for result in asr_results:
        if result.get('success'):
            print(f"    ✓ {result['file']}: '{result['transcription']}'")
        else:
            print(f"    ✗ {result['file']}: {result.get('error', 'No transcription')}")
    
    print(f"\n🗣️ TTS Results:")
    tts_success = sum(1 for r in tts_results if r.get('success', False))
    print(f"  Successful generations: {tts_success}/{len(tts_results)}")
    
    print(f"\n🔄 Round Trip Results:")
    rt_success = sum(1 for r in roundtrip_results if r.get('success', False))
    avg_similarity = np.mean([r.get('similarity', 0) for r in roundtrip_results if r.get('success')])
    print(f"  Successful round trips: {rt_success}/{len(roundtrip_results)}")
    print(f"  Average similarity: {avg_similarity:.2%}")
    
    for result in roundtrip_results:
        if result.get('success'):
            print(f"    {result['similarity']:.1%}: '{result['original']}' -> '{result['transcribed']}'")
    
    # Overall assessment
    print(f"\n🎯 Overall Assessment:")
    if asr_success > 0 and tts_success > 0:
        print("  ✅ Basic functionality working")
        if avg_similarity > 0.5:
            print("  ✅ Good speech quality and recognition")
        else:
            print("  ⚠️  Speech quality or recognition needs improvement")
    else:
        print("  ❌ Core functionality issues detected")
    
    return asr_success > 0 and tts_success > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
