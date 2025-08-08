"""
Sound feedback system for JARVIS
"""

import numpy as np
# Optional dependency: pyaudio may be unavailable
try:
    import pyaudio  # type: ignore
except Exception:  # pragma: no cover
    pyaudio = None  # type: ignore
import threading
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SoundFeedback:
    """Generate and play audio feedback sounds"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.audio = None
        self._initialize_audio()
    
    def _initialize_audio(self):
        """Initialize PyAudio"""
        if pyaudio is None:
            logger.warning("PyAudio not available. Sound feedback disabled.")
            self.audio = None
            return
        try:
            self.audio = pyaudio.PyAudio()
            logger.debug("Audio feedback system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio feedback: {e}")
            self.audio = None
    
    def _generate_tone(self, frequency: float, duration: float, volume: float = 0.3) -> np.ndarray:
        """Generate a pure tone"""
        frames = int(duration * self.sample_rate)
        t = np.linspace(0, duration, frames, False)
        
        # Generate sine wave
        wave = np.sin(2 * np.pi * frequency * t) * volume
        
        # Apply fade in/out to prevent clicks
        fade_frames = int(0.01 * self.sample_rate)  # 10ms fade
        if fade_frames > 0:
            fade_in = np.linspace(0, 1, fade_frames)
            fade_out = np.linspace(1, 0, fade_frames)
            
            wave[:fade_frames] *= fade_in
            wave[-fade_frames:] *= fade_out
        
        return wave.astype(np.float32)
    
    def _generate_beep_sequence(self, frequencies: list, durations: list, gaps: list, volume: float = 0.3) -> np.ndarray:
        """Generate a sequence of beeps"""
        if len(frequencies) != len(durations) or len(frequencies) != len(gaps):
            raise ValueError("Frequencies, durations, and gaps must have same length")
        
        segments = []
        
        for i, (freq, dur, gap) in enumerate(zip(frequencies, durations, gaps)):
            # Add the tone
            tone = self._generate_tone(freq, dur, volume)
            segments.append(tone)
            
            # Add gap (silence) except after last tone
            if i < len(frequencies) - 1 and gap > 0:
                silence_frames = int(gap * self.sample_rate)
                silence = np.zeros(silence_frames, dtype=np.float32)
                segments.append(silence)
        
        return np.concatenate(segments)
    
    def _play_audio(self, audio_data: np.ndarray):
        """Play audio data"""
        if self.audio is None:
            logger.debug("Audio system not initialized; skipping feedback playback")
            return
        
        try:
            stream = self.audio.open(
                format=getattr(pyaudio, "paFloat32", 1),
                channels=1,
                rate=self.sample_rate,
                output=True
            )
            
            stream.write(audio_data.tobytes())
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            logger.error(f"Error playing audio feedback: {e}")
    
    def play_listening_start(self):
        """Play sound when starting to listen"""
        # Rising tone: 400Hz to 800Hz
        tone = self._generate_beep_sequence([400, 600], [0.1, 0.1], [0.05, 0], volume=0.2)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_listening_stop(self):
        """Play sound when stopping listening"""
        # Falling tone: 800Hz to 400Hz
        tone = self._generate_beep_sequence([800, 600], [0.1, 0.1], [0.05, 0], volume=0.2)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_processing(self):
        """Play sound when processing speech"""
        # Quick double beep: 1000Hz
        tone = self._generate_beep_sequence([1000, 1000], [0.05, 0.05], [0.05, 0], volume=0.15)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_success(self):
        """Play sound for successful operation"""
        # Rising chord: 523Hz (C), 659Hz (E), 784Hz (G)
        tone = self._generate_beep_sequence([523, 659, 784], [0.1, 0.1, 0.2], [0.02, 0.02, 0], volume=0.2)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_error(self):
        """Play sound for error"""
        # Low descending tone: 300Hz to 200Hz
        tone = self._generate_beep_sequence([300, 250, 200], [0.15, 0.15, 0.2], [0.05, 0.05, 0], volume=0.25)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_camera_click(self):
        """Play camera shutter sound"""
        # Sharp click: 2000Hz very brief
        tone = self._generate_beep_sequence([2000], [0.03], [0], volume=0.3)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_startup(self):
        """Play startup sound"""
        # Ascending arpeggio: C-E-G-C
        tone = self._generate_beep_sequence([261, 329, 392, 523], [0.15, 0.15, 0.15, 0.3], [0.05, 0.05, 0.05, 0], volume=0.2)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_shutdown(self):
        """Play shutdown sound"""
        # Descending arpeggio: C-G-E-C
        tone = self._generate_beep_sequence([523, 392, 329, 261], [0.15, 0.15, 0.15, 0.3], [0.05, 0.05, 0.05, 0], volume=0.2)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_voice_detected(self):
        """Play sound when voice is first detected"""
        # Single rising tone
        tone = self._generate_beep_sequence([600], [0.08], [0], volume=0.15)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def play_thinking(self):
        """Play sound while AI is thinking"""
        # Gentle pulsing tone
        tone = self._generate_beep_sequence([440, 440, 440], [0.1, 0.1, 0.1], [0.1, 0.1, 0], volume=0.1)
        threading.Thread(target=self._play_audio, args=(tone,), daemon=True).start()
    
    def cleanup(self):
        """Cleanup audio resources"""
        if self.audio:
            try:
                self.audio.terminate()
            except Exception:
                pass
            self.audio = None

# Global sound feedback instance
sound_feedback = SoundFeedback()

# Convenience functions
def play_listening_start():
    sound_feedback.play_listening_start()

def play_listening_stop():
    sound_feedback.play_listening_stop()

def play_processing():
    sound_feedback.play_processing()

def play_success():
    sound_feedback.play_success()

def play_error():
    sound_feedback.play_error()

def play_camera_click():
    sound_feedback.play_camera_click()

def play_startup():
    sound_feedback.play_startup()

def play_shutdown():
    sound_feedback.play_shutdown()

def play_voice_detected():
    sound_feedback.play_voice_detected()

def play_thinking():
    sound_feedback.play_thinking()
