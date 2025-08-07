"""
JARVIS Parallel Processing Manager - Coordinates all system components
"""

import time
import threading
import logging
import queue
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .task_queue import task_queue, TaskType, TaskPriority, TaskStatus
from .audio_manager import get_audio_manager
from .camera_manager import get_camera_manager
from ..audio.asr import ASRManager
from ..audio.tts import TTSManager
from ..config.config import config

logger = logging.getLogger(__name__)

class SystemState(Enum):
    """Overall system state"""
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    RUNNING = "running"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"

@dataclass
class SystemStatus:
    """System status information"""
    state: SystemState
    audio_available: bool
    camera_available: bool
    asr_available: bool
    tts_available: bool
    uptime: float
    tasks_completed: int
    tasks_failed: int

class ParallelJARVIS:
    """Main JARVIS system with parallel processing architecture"""
    
    def __init__(self, speech_callback: Optional[Callable] = None):
        self.state = SystemState.STOPPED
        self.start_time = time.time()
        
        # Component managers
        self.audio_manager = get_audio_manager()
        self.camera_manager = get_camera_manager()
        self.asr_manager = None
        self.tts_manager = None
        
        # Set speech callback
        if speech_callback:
            self.audio_manager.speech_callback = self._handle_speech_input
            self.external_speech_callback = speech_callback
        else:
            self.external_speech_callback = None
        
        # System threads
        self.monitor_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            'commands_processed': 0,
            'photos_taken': 0,
            'errors_recovered': 0,
            'uptime_start': time.time()
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info("ParallelJARVIS initialized")
    
    def initialize(self) -> bool:
        """Initialize all system components"""
        with self.lock:
            if self.state == SystemState.INITIALIZING:
                logger.warning("System already initializing")
                return False
            
            self.state = SystemState.INITIALIZING
        
        logger.info("Initializing JARVIS system components...")
        
        try:
            # Start task queue
            task_queue.start()
            
            # Initialize ASR and TTS
            logger.info("Loading speech models...")
            self.asr_manager = ASRManager()
            self.tts_manager = TTSManager()
            
            # Initialize audio system
            logger.info("Initializing audio system...")
            if not self.audio_manager.initialize():
                logger.warning("Audio system initialization failed, continuing without audio")
            
            # Initialize camera system
            logger.info("Initializing camera system...")
            if not self.camera_manager.initialize():
                logger.warning("Camera system initialization failed, continuing without camera")
            
            with self.lock:
                self.state = SystemState.RUNNING
            
            logger.info("JARVIS system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            
            with self.lock:
                self.state = SystemState.ERROR
            
            return False
    
    def start(self) -> bool:
        """Start the JARVIS system"""
        if not self.initialize():
            return False
        
        try:
            self.running = True
            
            # Start audio listening
            if self.audio_manager.state.value in ['ready', 'stopped']:
                self.audio_manager.start_listening()
            
            # Start camera capture
            if self.camera_manager.state.value in ['ready', 'stopped']:
                self.camera_manager.start_capture()
            
            # Start system monitor
            self.monitor_thread = threading.Thread(
                target=self._system_monitor_loop,
                name="JARVIS-Monitor",
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("JARVIS system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start JARVIS system: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the JARVIS system"""
        logger.info("Stopping JARVIS system...")
        
        with self.lock:
            self.state = SystemState.SHUTTING_DOWN
            self.running = False
        
        # Stop components
        if self.audio_manager:
            self.audio_manager.stop_listening()
        
        if self.camera_manager:
            self.camera_manager.stop_capture()
        
        # Stop task queue
        task_queue.stop()
        
        # Wait for monitor thread
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        with self.lock:
            self.state = SystemState.STOPPED
        
        logger.info("JARVIS system stopped")
    
    def process_text_command(self, text: str) -> str:
        """Process a text command"""
        task_id = task_queue.submit_task(
            TaskType.TEXT_COMMAND,
            self._process_command_internal,
            (text,),
            priority=TaskPriority.NORMAL,
            timeout=30.0
        )
        
        # Wait for result
        max_wait = 30.0
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = task_queue.get_task_status(task_id)
            if status == TaskStatus.COMPLETED:
                result = task_queue.get_task_result(task_id)
                return result if result else "No response generated"
            elif status == TaskStatus.FAILED:
                return "Error processing command"
            
            time.sleep(0.1)
        
        return "Command timed out"
    
    def take_photo(self) -> Dict[str, Any]:
        """Take a photo"""
        task_id = task_queue.submit_task(
            TaskType.PHOTO_CAPTURE,
            self._take_photo_internal,
            priority=TaskPriority.NORMAL,
            timeout=10.0
        )
        
        # Wait for result
        max_wait = 10.0
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = task_queue.get_task_status(task_id)
            if status == TaskStatus.COMPLETED:
                result = task_queue.get_task_result(task_id)
                return result if result else {"success": False, "message": "Unknown error"}
            elif status == TaskStatus.FAILED:
                return {"success": False, "message": "Photo capture failed"}
            
            time.sleep(0.1)
        
        return {"success": False, "message": "Photo capture timed out"}
    
    def get_camera_frame(self) -> Optional[bytes]:
        """Get current camera frame as JPEG bytes"""
        if self.camera_manager.state.value != 'capturing':
            return None
        
        frame = self.camera_manager.get_current_frame()
        if frame is not None:
            import cv2
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return buffer.tobytes()
        
        return None
    
    def get_system_status(self) -> SystemStatus:
        """Get comprehensive system status"""
        with self.lock:
            uptime = time.time() - self.stats['uptime_start']
            queue_stats = task_queue.get_queue_stats()
            
            return SystemStatus(
                state=self.state,
                audio_available=self.audio_manager.state.value in ['ready', 'listening'],
                camera_available=self.camera_manager.state.value in ['ready', 'capturing'],
                asr_available=self.asr_manager is not None,
                tts_available=self.tts_manager is not None,
                uptime=uptime,
                tasks_completed=queue_stats['completed_tasks'],
                tasks_failed=queue_stats['failed_tasks']
            )
    
    def _handle_speech_input(self, audio_data):
        """Handle speech input from audio manager"""
        try:
            # Submit speech processing task
            task_queue.submit_task(
                TaskType.VOICE_COMMAND,
                self._process_speech_internal,
                (audio_data,),
                priority=TaskPriority.HIGH,
                timeout=30.0
            )
        except Exception as e:
            logger.error(f"Error handling speech input: {e}")
    
    def _process_speech_internal(self, audio_data):
        """Process speech data internally"""
        try:
            if not self.asr_manager:
                return "Speech recognition not available"
            
            # Transcribe speech
            transcription = self.asr_manager.transcribe(audio_data)
            
            if not transcription or not transcription.strip():
                return "No speech detected"
            
            logger.info(f"Speech transcribed: '{transcription}'")
            
            # Process command
            response = self._process_command_internal(transcription)
            
            # Speak response
            if response and self.tts_manager:
                task_queue.submit_task(
                    TaskType.TTS_SYNTHESIS,
                    self._speak_response,
                    (response,),
                    priority=TaskPriority.NORMAL,
                    timeout=15.0
                )
            
            # Call external callback if provided
            if self.external_speech_callback:
                self.external_speech_callback(audio_data)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing speech: {e}")
            return f"Error: {str(e)}"
    
    def _process_command_internal(self, text: str) -> str:
        """Process command internally"""
        try:
            with self.lock:
                self.stats['commands_processed'] += 1
            
            text = text.lower().strip()
            logger.info(f"Processing command: '{text}'")
            
            # Import command processor
            from ..commands.processor import CommandProcessor
            processor = CommandProcessor(self)
            
            return processor.process_command(text)
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return f"Error processing command: {str(e)}"
    
    def _take_photo_internal(self) -> Dict[str, Any]:
        """Take photo internally"""
        try:
            if self.camera_manager.state.value != 'capturing':
                return {"success": False, "message": "Camera not available"}
            
            photo_path = self.camera_manager.capture_photo()
            
            if photo_path:
                with self.lock:
                    self.stats['photos_taken'] += 1
                
                return {
                    "success": True,
                    "message": f"Photo saved as {photo_path.split('/')[-1]}",
                    "path": photo_path
                }
            else:
                return {"success": False, "message": "Failed to capture photo"}
                
        except Exception as e:
            logger.error(f"Error taking photo: {e}")
            return {"success": False, "message": str(e)}
    
    def _speak_response(self, text: str):
        """Speak response using TTS"""
        try:
            if self.tts_manager:
                self.tts_manager.speak(text, play_audio=True)
        except Exception as e:
            logger.error(f"Error speaking response: {e}")
    
    def _system_monitor_loop(self):
        """System monitoring loop"""
        logger.info("System monitor started")
        
        while self.running:
            try:
                # Check component health
                self._check_component_health()
                
                # Log system statistics periodically
                if int(time.time()) % 60 == 0:  # Every minute
                    self._log_system_stats()
                
                time.sleep(5.0)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in system monitor: {e}")
                time.sleep(1.0)
        
        logger.info("System monitor stopped")
    
    def _check_component_health(self):
        """Check health of all components"""
        # Check audio manager
        if (self.audio_manager.state.value == 'error' and 
            time.time() - self.audio_manager.last_error_time > 30):
            logger.info("Attempting audio system recovery")
            self.audio_manager._attempt_recovery()
        
        # Check camera manager
        if (self.camera_manager.state.value == 'error' and 
            time.time() - self.camera_manager.last_error_time > 30):
            logger.info("Attempting camera system recovery")
            self.camera_manager._attempt_recovery()
    
    def _log_system_stats(self):
        """Log system statistics"""
        status = self.get_system_status()
        queue_stats = task_queue.get_queue_stats()
        
        logger.info(f"System Stats - Uptime: {status.uptime:.1f}s, "
                   f"Commands: {self.stats['commands_processed']}, "
                   f"Photos: {self.stats['photos_taken']}, "
                   f"Queue: {queue_stats['queue_size']} pending, "
                   f"Tasks: {queue_stats['completed_tasks']} completed")

# Global parallel JARVIS instance
parallel_jarvis = None

def get_jarvis_instance() -> ParallelJARVIS:
    """Get global JARVIS instance"""
    global parallel_jarvis
    if parallel_jarvis is None:
        parallel_jarvis = ParallelJARVIS()
    return parallel_jarvis
