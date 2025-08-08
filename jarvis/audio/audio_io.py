"""
Audio Input/Output handling for JARVIS
"""

# Optional dependency: pyaudio may be unavailable in CI/minimal envs
try:
    import pyaudio  # type: ignore
except Exception:  # pragma: no cover
    pyaudio = None  # type: ignore

import numpy as np
import threading
import time
import logging
import wave
import os
from typing import Optional, Callable, List
from collections import deque

from ..config.config import config
from .sounds import play_listening_start, play_listening_stop, play_voice_detected, play_processing

logger = logging.getLogger(__name__)

class AudioRecorder:
    """Real-time audio recording with voice activity detection"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.is_recording = False
        self.audio_buffer = deque(maxlen=1000)  # Store recent audio chunks
        
        # Audio settings
        self.sample_rate = config.audio.sample_rate
        self.chunk_size = config.audio.chunk_size
        self.channels = config.audio.channels
        self.format = getattr(pyaudio, "paInt16", 8) if pyaudio else 8
        
        # Voice Activity Detection
        self.vad_threshold = config.audio.vad_threshold
        self.silence_duration = config.audio.silence_duration
        self.min_recording_duration = 0.5  # Minimum recording time
        
        # PyAudio setup
        self.audio = pyaudio.PyAudio() if pyaudio else None
        self.stream = None
        self.recording_thread = None
        
        # Recording state
        self.current_recording = []
        self.last_voice_time = 0
        self.recording_start_time = 0
    
    def start_recording(self):
        """Start continuous audio recording"""
        if self.is_recording:
            return
        
        if self.audio is None:
            logger.warning("PyAudio not available. Audio recording disabled.")
            return
        
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.stream.start_stream()
            logger.info("Audio recording started")
            
        except Exception as e:
            logger.error(f"Failed to start audio recording: {e}")
    
    def stop_recording(self):
        """Stop audio recording"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self.stream = None
        
        logger.info("Audio recording stopped")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for processing audio chunks"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Convert audio data to numpy array
        audio_chunk = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Add to buffer
        self.audio_buffer.append(audio_chunk)
        
        # Voice Activity Detection
        if self._detect_voice_activity(audio_chunk):
            self.last_voice_time = time.time()

            # Start new recording if not already recording
            if not self.current_recording:
                self.recording_start_time = time.time()
                print("🎙️ Listening... (speak now)")
                play_voice_detected()  # Audio feedback for voice detection
                logger.debug("Voice detected, starting recording")

            self.current_recording.append(audio_chunk)
        
        # Check if we should stop recording (silence detected)
        elif self.current_recording:
            current_time = time.time()
            silence_time = current_time - self.last_voice_time
            recording_duration = current_time - self.recording_start_time
            
            if (silence_time >= self.silence_duration and
                recording_duration >= self.min_recording_duration):

                print("🔇 Silence detected, processing speech...")
                play_processing()  # Audio feedback for processing
                # Process the recorded audio
                self._process_recording()
        
        return (in_data, getattr(pyaudio, "paContinue", 0))
    
    def _detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Simple voice activity detection based on energy"""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        is_voice = rms > self.vad_threshold

        # Debug output for voice activity
        if config.debug and is_voice:
            print(f"🎵 Voice activity: RMS={rms:.4f} (threshold={self.vad_threshold:.4f})")

        return is_voice
    
    def _process_recording(self):
        """Process completed recording"""
        if not self.current_recording:
            return
        
        # Combine audio chunks
        audio_data = np.concatenate(self.current_recording)
        
        logger.info(f"Processing recording: {len(audio_data)} samples, "
                   f"{len(audio_data) / self.sample_rate:.2f} seconds")
        
        # Call callback if provided
        if self.callback:
            try:
                self.callback(audio_data)
            except Exception as e:
                logger.error(f"Error in recording callback: {e}")
        
        # Clear current recording
        self.current_recording = []
    
    def save_recording_to_file(self, audio_data: np.ndarray, filename: str):
        """Save audio data to WAV file"""
        try:
            # Convert to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            if self.audio is None:
                logger.warning("PyAudio not available; cannot determine sample width accurately. Using 2 bytes.")
                sample_width = 2
            else:
                sample_width = self.audio.get_sample_size(self.format)
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            logger.info(f"Audio saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving audio to {filename}: {e}")
    
    def get_recent_audio(self, duration_seconds: float = 5.0) -> np.ndarray:
        """Get recent audio from buffer"""
        chunks_needed = int(duration_seconds * self.sample_rate / self.chunk_size)
        recent_chunks = list(self.audio_buffer)[-chunks_needed:]
        
        if recent_chunks:
            return np.concatenate(recent_chunks)
        else:
            return np.array([])
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_recording()
        if hasattr(self, 'audio') and self.audio is not None:
            try:
                self.audio.terminate()
            except Exception:
                pass

class AudioPlayer:
    """Audio playback system"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio() if pyaudio else None
        self.is_playing = False
    
    def play_audio_data(self, audio_data: np.ndarray, sample_rate: Optional[int] = None):
        """Play audio data directly"""
        if self.audio is None:
            logger.warning("PyAudio not available. Skipping audio playback.")
            return
        if sample_rate is None:
            sample_rate = config.audio.sample_rate
        
        try:
            # Convert to int16 if needed
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            stream = self.audio.open(
                format=getattr(pyaudio, "paInt16", 8),
                channels=1,
                rate=sample_rate,
                output=True
            )
            
            self.is_playing = True
            stream.write(audio_data.tobytes())
            stream.stop_stream()
            stream.close()
            self.is_playing = False
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            self.is_playing = False
    
    def play_audio_file(self, filename: str):
        """Play audio from file"""
        if self.audio is None:
            logger.warning("PyAudio not available. Skipping audio file playback.")
            return
        try:
            with wave.open(filename, 'rb') as wf:
                # Get audio parameters
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                
                # Create stream
                stream = self.audio.open(
                    format=self.audio.get_format_from_width(sample_width),
                    channels=channels,
                    rate=sample_rate,
                    output=True
                )
                
                # Play audio
                self.is_playing = True
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                
                while data and self.is_playing:
                    stream.write(data)
                    data = wf.readframes(chunk_size)
                
                stream.stop_stream()
                stream.close()
                self.is_playing = False
                
        except Exception as e:
            logger.error(f"Error playing audio file {filename}: {e}")
            self.is_playing = False
    
    def stop_playback(self):
        """Stop current playback"""
        self.is_playing = False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'audio') and self.audio is not None:
            try:
                self.audio.terminate()
            except Exception:
                pass

class AudioManager:
    """High-level audio management"""
    
    def __init__(self, speech_callback: Optional[Callable] = None):
        self.recorder = AudioRecorder(callback=speech_callback)
        self.player = AudioPlayer()
        self.temp_dir = config.audio.temp_audio_dir
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def start_listening(self):
        """Start listening for voice input"""
        self.recorder.start_recording()
    
    def stop_listening(self):
        """Stop listening for voice input"""
        self.recorder.stop_recording()
    
    def play_audio(self, audio_input):
        """Play audio (file path or audio data)"""
        if isinstance(audio_input, str):
            self.player.play_audio_file(audio_input)
        elif isinstance(audio_input, np.ndarray):
            self.player.play_audio_data(audio_input)
        else:
            logger.error(f"Unsupported audio input type: {type(audio_input)}")
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.recorder.is_recording
    
    def is_playing(self) -> bool:
        """Check if currently playing audio"""
        return self.player.is_playing
    
    def get_status(self) -> dict:
        """Get audio system status"""
        return {
            "recording": self.is_recording(),
            "playing": self.is_playing(),
            "sample_rate": config.audio.sample_rate,
            "channels": config.audio.channels
        }
