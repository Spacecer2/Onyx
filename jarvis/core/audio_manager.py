"""
JARVIS Robust Audio Manager - Reliable voice listening with error handling and retry logic
"""

import time
import threading
import logging
import queue
import numpy as np
import pyaudio
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ..config.config import config
from .task_queue import task_queue, TaskType, TaskPriority

logger = logging.getLogger(__name__)

class AudioState(Enum):
    """Audio system states"""
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    READY = "ready"
    LISTENING = "listening"
    ERROR = "error"
    RECOVERING = "recovering"

@dataclass
class AudioConfig:
    """Audio configuration with fallback options"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: int = pyaudio.paInt16
    input_device_index: Optional[int] = None
    
    # Fallback configurations
    fallback_sample_rates: list = None
    fallback_chunk_sizes: list = None
    
    def __post_init__(self):
        if self.fallback_sample_rates is None:
            self.fallback_sample_rates = [16000, 44100, 22050, 8000]
        if self.fallback_chunk_sizes is None:
            self.fallback_chunk_sizes = [1024, 2048, 512, 4096]

class RobustAudioManager:
    """Robust audio manager with automatic recovery and retry logic"""
    
    def __init__(self, speech_callback: Optional[Callable] = None):
        self.speech_callback = speech_callback
        self.config = AudioConfig()
        
        # Audio system
        self.pyaudio_instance = None
        self.stream = None
        self.state = AudioState.STOPPED
        
        # Voice activity detection
        self.vad_threshold = config.audio.vad_threshold
        self.silence_duration = config.audio.silence_duration
        self.min_recording_duration = config.audio.min_recording_duration
        
        # Recording state
        self.current_recording = []
        self.recording_start_time = 0
        self.last_voice_time = 0
        self.is_recording = False
        
        # Threading
        self.audio_thread = None
        self.processing_thread = None
        self.audio_queue = queue.Queue(maxsize=100)
        self.running = False
        
        # Error handling
        self.initialization_attempts = 0
        self.max_init_attempts = 5
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        self.last_error_time = 0
        self.error_cooldown = 5.0  # seconds
        
        # Statistics
        self.stats = {
            'total_recordings': 0,
            'successful_recordings': 0,
            'failed_recordings': 0,
            'recovery_count': 0,
            'uptime_start': time.time()
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info("RobustAudioManager initialized")
    
    def initialize(self) -> bool:
        """Initialize audio system with retry logic"""
        with self.lock:
            if self.state == AudioState.INITIALIZING:
                logger.warning("Audio system already initializing")
                return False
            
            self.state = AudioState.INITIALIZING
            self.initialization_attempts += 1
        
        logger.info(f"Initializing audio system (attempt {self.initialization_attempts})")
        
        try:
            # Initialize PyAudio
            if self.pyaudio_instance is None:
                self.pyaudio_instance = pyaudio.PyAudio()
            
            # Find best audio configuration
            if not self._find_working_audio_config():
                raise RuntimeError("No working audio configuration found")
            
            # Test audio input
            if not self._test_audio_input():
                raise RuntimeError("Audio input test failed")
            
            with self.lock:
                self.state = AudioState.READY
                self.initialization_attempts = 0
            
            logger.info("Audio system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Audio initialization failed: {e}")
            
            with self.lock:
                self.state = AudioState.ERROR
            
            # Schedule retry if not exceeded max attempts
            if self.initialization_attempts < self.max_init_attempts:
                retry_delay = min(2 ** self.initialization_attempts, 30)  # Exponential backoff
                logger.info(f"Retrying audio initialization in {retry_delay}s")
                
                task_queue.submit_task(
                    TaskType.AUDIO_INIT,
                    self._delayed_retry_init,
                    (retry_delay,),
                    priority=TaskPriority.HIGH,
                    timeout=60.0
                )
            else:
                logger.error("Max audio initialization attempts reached")
            
            return False
    
    def start_listening(self) -> bool:
        """Start voice listening with error handling"""
        with self.lock:
            if self.state not in [AudioState.READY, AudioState.STOPPED]:
                if self.state == AudioState.ERROR:
                    logger.info("Attempting to recover from error state")
                    if not self._attempt_recovery():
                        return False
                else:
                    logger.warning(f"Cannot start listening in state: {self.state}")
                    return False
            
            if self.running:
                logger.warning("Audio listening already running")
                return True
        
        try:
            # Create audio stream
            self.stream = self.pyaudio_instance.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.input_device_index,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback,
                start=False
            )
            
            # Start threads
            self.running = True
            self.audio_thread = threading.Thread(
                target=self._audio_processing_loop,
                name="JARVIS-Audio",
                daemon=True
            )
            self.processing_thread = threading.Thread(
                target=self._speech_processing_loop,
                name="JARVIS-Speech",
                daemon=True
            )
            
            self.audio_thread.start()
            self.processing_thread.start()
            
            # Start audio stream
            self.stream.start_stream()
            
            with self.lock:
                self.state = AudioState.LISTENING
            
            logger.info("Voice listening started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start voice listening: {e}")
            self._cleanup_audio_resources()
            
            with self.lock:
                self.state = AudioState.ERROR
            
            # Attempt recovery
            self._attempt_recovery()
            return False
    
    def stop_listening(self):
        """Stop voice listening"""
        logger.info("Stopping voice listening")
        
        with self.lock:
            self.running = False
        
        # Stop audio stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self.stream = None
        
        # Wait for threads to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=5.0)
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        with self.lock:
            self.state = AudioState.STOPPED
        
        logger.info("Voice listening stopped")
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.stop_listening()
        self._cleanup_audio_resources()
    
    def get_status(self) -> Dict[str, Any]:
        """Get audio system status"""
        with self.lock:
            uptime = time.time() - self.stats['uptime_start']
            
            return {
                'state': self.state.value,
                'available': self.state in [AudioState.READY, AudioState.LISTENING],
                'listening': self.state == AudioState.LISTENING,
                'recording': self.is_recording,
                'config': {
                    'sample_rate': self.config.sample_rate,
                    'channels': self.config.channels,
                    'chunk_size': self.config.chunk_size
                },
                'stats': {
                    **self.stats,
                    'uptime': uptime,
                    'success_rate': (
                        self.stats['successful_recordings'] / 
                        max(self.stats['total_recordings'], 1)
                    )
                }
            }
    
    def _find_working_audio_config(self) -> bool:
        """Find a working audio configuration"""
        logger.debug("Finding working audio configuration")
        
        # Try different sample rates
        for sample_rate in self.config.fallback_sample_rates:
            for chunk_size in self.config.fallback_chunk_sizes:
                try:
                    # Test configuration
                    test_stream = self.pyaudio_instance.open(
                        format=self.config.format,
                        channels=self.config.channels,
                        rate=sample_rate,
                        input=True,
                        input_device_index=self.config.input_device_index,
                        frames_per_buffer=chunk_size,
                        start=False
                    )
                    
                    # Test reading data
                    test_stream.start_stream()
                    data = test_stream.read(chunk_size, exception_on_overflow=False)
                    test_stream.stop_stream()
                    test_stream.close()
                    
                    # Configuration works
                    self.config.sample_rate = sample_rate
                    self.config.chunk_size = chunk_size
                    
                    logger.info(f"Found working audio config: {sample_rate}Hz, {chunk_size} chunk")
                    return True
                    
                except Exception as e:
                    logger.debug(f"Audio config failed: {sample_rate}Hz, {chunk_size} chunk - {e}")
                    continue
        
        logger.error("No working audio configuration found")
        return False
    
    def _test_audio_input(self) -> bool:
        """Test audio input functionality"""
        try:
            logger.debug("Testing audio input")
            
            test_stream = self.pyaudio_instance.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.input_device_index,
                frames_per_buffer=self.config.chunk_size
            )
            
            # Read a few chunks to test
            for _ in range(5):
                data = test_stream.read(self.config.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Check if we're getting reasonable audio data
                if len(audio_data) == 0:
                    raise RuntimeError("No audio data received")
                
                # Check for reasonable signal levels
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                if rms > 32767:  # Clipping
                    logger.warning("Audio input may be clipping")
            
            test_stream.close()
            logger.debug("Audio input test passed")
            return True
            
        except Exception as e:
            logger.error(f"Audio input test failed: {e}")
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio stream callback"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        try:
            # Convert to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Add to processing queue
            if not self.audio_queue.full():
                self.audio_queue.put(audio_data, block=False)
            else:
                logger.warning("Audio queue full, dropping frame")
            
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")
        
        return (None, pyaudio.paContinue)
    
    def _audio_processing_loop(self):
        """Main audio processing loop"""
        logger.info("Audio processing loop started")
        
        while self.running:
            try:
                # Get audio data from queue
                try:
                    audio_chunk = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process audio chunk
                self._process_audio_chunk(audio_chunk)
                
            except Exception as e:
                logger.error(f"Error in audio processing loop: {e}")
                time.sleep(0.1)
        
        logger.info("Audio processing loop stopped")
    
    def _process_audio_chunk(self, audio_chunk: np.ndarray):
        """Process a single audio chunk"""
        # Voice Activity Detection
        if self._detect_voice_activity(audio_chunk):
            self.last_voice_time = time.time()
            
            # Start new recording if not already recording
            if not self.is_recording:
                self.recording_start_time = time.time()
                self.current_recording = []
                self.is_recording = True
                logger.debug("Voice detected, starting recording")
            
            self.current_recording.append(audio_chunk)
        
        # Check if we should stop recording
        elif self.is_recording:
            silence_time = time.time() - self.last_voice_time
            recording_duration = time.time() - self.recording_start_time
            
            if (silence_time >= self.silence_duration and 
                recording_duration >= self.min_recording_duration):
                
                logger.debug("Silence detected, processing speech")
                self._finalize_recording()
    
    def _detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Detect voice activity in audio chunk"""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
        return rms > self.vad_threshold * 32767  # Scale threshold for int16
    
    def _finalize_recording(self):
        """Finalize current recording and submit for processing"""
        if not self.current_recording:
            return
        
        # Combine audio chunks
        audio_data = np.concatenate(self.current_recording)
        
        # Reset recording state
        self.is_recording = False
        self.current_recording = []
        
        # Update statistics
        with self.lock:
            self.stats['total_recordings'] += 1
        
        # Submit for speech processing
        task_queue.submit_task(
            TaskType.VOICE_COMMAND,
            self._process_speech_data,
            (audio_data,),
            priority=TaskPriority.HIGH,
            callback=self._on_speech_success,
            error_callback=self._on_speech_error,
            timeout=30.0
        )
    
    def _process_speech_data(self, audio_data: np.ndarray):
        """Process speech data (runs in task queue)"""
        if self.speech_callback:
            return self.speech_callback(audio_data)
        return None
    
    def _on_speech_success(self, result):
        """Handle successful speech processing"""
        with self.lock:
            self.stats['successful_recordings'] += 1
        logger.debug("Speech processing completed successfully")
    
    def _on_speech_error(self, error):
        """Handle speech processing error"""
        with self.lock:
            self.stats['failed_recordings'] += 1
        logger.error(f"Speech processing failed: {error}")
    
    def _speech_processing_loop(self):
        """Speech processing loop (placeholder for future enhancements)"""
        logger.info("Speech processing loop started")
        
        while self.running:
            time.sleep(1.0)  # Currently just a placeholder
        
        logger.info("Speech processing loop stopped")
    
    def _attempt_recovery(self) -> bool:
        """Attempt to recover from error state"""
        if time.time() - self.last_error_time < self.error_cooldown:
            logger.debug("Still in error cooldown period")
            return False
        
        with self.lock:
            self.recovery_attempts += 1
            self.stats['recovery_count'] += 1
            
            if self.recovery_attempts > self.max_recovery_attempts:
                logger.error("Max recovery attempts reached")
                return False
            
            self.state = AudioState.RECOVERING
        
        logger.info(f"Attempting audio system recovery (attempt {self.recovery_attempts})")
        
        try:
            # Cleanup existing resources
            self._cleanup_audio_resources()
            
            # Wait a moment
            time.sleep(1.0)
            
            # Reinitialize
            if self.initialize():
                with self.lock:
                    self.recovery_attempts = 0
                logger.info("Audio system recovery successful")
                return True
            else:
                raise RuntimeError("Recovery initialization failed")
                
        except Exception as e:
            logger.error(f"Audio system recovery failed: {e}")
            
            with self.lock:
                self.state = AudioState.ERROR
                self.last_error_time = time.time()
            
            return False
    
    def _cleanup_audio_resources(self):
        """Cleanup audio resources"""
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error cleaning up audio stream: {e}")
            finally:
                self.stream = None
        
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            finally:
                self.pyaudio_instance = None
    
    def _delayed_retry_init(self, delay: float):
        """Delayed initialization retry"""
        time.sleep(delay)
        self.initialize()

# Global robust audio manager instance
robust_audio_manager = None

def get_audio_manager() -> RobustAudioManager:
    """Get global audio manager instance"""
    global robust_audio_manager
    if robust_audio_manager is None:
        robust_audio_manager = RobustAudioManager()
    return robust_audio_manager
