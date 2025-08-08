"""
JARVIS Robust Camera Manager - Reliable camera access with frame buffering and retry logic
"""

import time
import threading
import logging
import queue
# Optional dependency: OpenCV might be unavailable in CI/minimal envs
try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore
import numpy as np
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import os

from ..config.config import config
from .task_queue import task_queue, TaskType, TaskPriority

logger = logging.getLogger(__name__)

class CameraState(Enum):
    """Camera system states"""
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    READY = "ready"
    CAPTURING = "capturing"
    ERROR = "error"
    RECOVERING = "recovering"
    DISABLED = "disabled"

@dataclass
class CameraConfig:
    """Camera configuration with fallback options"""
    camera_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    
    # Fallback configurations
    fallback_indices: List[int] = None
    fallback_resolutions: List[tuple] = None
    fallback_fps: List[int] = None
    
    def __post_init__(self):
        if self.fallback_indices is None:
            self.fallback_indices = [0, 1, 2, -1]  # -1 for any available
        if self.fallback_resolutions is None:
            self.fallback_resolutions = [
                (640, 480), (1280, 720), (320, 240), (800, 600)
            ]
        if self.fallback_fps is None:
            self.fallback_fps = [30, 15, 10, 5]

@dataclass
class CameraFrame:
    """Represents a camera frame with metadata"""
    frame: np.ndarray
    timestamp: float
    frame_id: int
    width: int
    height: int

class RobustCameraManager:
    """Robust camera manager with frame buffering and automatic recovery"""
    
    def __init__(self):
        self.config = CameraConfig()
        
        # Camera system
        self.camera = None
        self.state = CameraState.STOPPED if cv2 is not None else CameraState.DISABLED
        
        # Frame buffering
        self.frame_buffer = queue.Queue(maxsize=30)  # 1 second at 30fps
        self.current_frame = None
        self.frame_counter = 0
        
        # Threading
        self.capture_thread = None
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
            'total_frames': 0,
            'successful_captures': 0,
            'failed_captures': 0,
            'photos_taken': 0,
            'recovery_count': 0,
            'uptime_start': time.time(),
            'fps_actual': 0.0
        }
        
        # FPS calculation
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Photo storage
        self.photos_dir = Path("jarvis/photos")
        self.photos_dir.mkdir(exist_ok=True)
        
        logger.info("RobustCameraManager initialized")
    
    def initialize(self) -> bool:
        """Initialize camera system with retry logic"""
        if cv2 is None:
            logger.warning("OpenCV not available. Camera subsystem disabled.")
            with self.lock:
                self.state = CameraState.DISABLED
            return False
        with self.lock:
            if self.state == CameraState.INITIALIZING:
                logger.warning("Camera system already initializing")
                return False
            
            self.state = CameraState.INITIALIZING
            self.initialization_attempts += 1
        
        logger.info(f"Initializing camera system (attempt {self.initialization_attempts})")
        
        try:
            # Find working camera configuration
            if not self._find_working_camera_config():
                raise RuntimeError("No working camera configuration found")
            
            # Test camera capture
            if not self._test_camera_capture():
                raise RuntimeError("Camera capture test failed")
            
            with self.lock:
                self.state = CameraState.READY
                self.initialization_attempts = 0
            
            logger.info("Camera system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            
            with self.lock:
                self.state = CameraState.ERROR
            
            # Schedule retry if not exceeded max attempts
            if self.initialization_attempts < self.max_init_attempts:
                retry_delay = min(2 ** self.initialization_attempts, 30)  # Exponential backoff
                logger.info(f"Retrying camera initialization in {retry_delay}s")
                
                task_queue.submit_task(
                    TaskType.CAMERA_INIT,
                    self._delayed_retry_init,
                    (retry_delay,),
                    priority=TaskPriority.HIGH,
                    timeout=60.0
                )
            else:
                logger.error("Max camera initialization attempts reached")
            
            return False
    
    def start_capture(self) -> bool:
        """Start camera capture with error handling"""
        if cv2 is None:
            logger.warning("OpenCV not available. Cannot start capture.")
            return False
        with self.lock:
            if self.state not in [CameraState.READY, CameraState.STOPPED]:
                if self.state == CameraState.ERROR:
                    logger.info("Attempting to recover from error state")
                    if not self._attempt_recovery():
                        return False
                else:
                    logger.warning(f"Cannot start capture in state: {self.state}")
                    return False
            
            if self.running:
                logger.warning("Camera capture already running")
                return True
        
        try:
            # Open camera
            self.camera = cv2.VideoCapture(self.config.camera_index)
            
            if not self.camera.isOpened():
                raise RuntimeError(f"Failed to open camera {self.config.camera_index}")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Start capture thread
            self.running = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                name="JARVIS-Camera",
                daemon=True
            )
            self.capture_thread.start()
            
            with self.lock:
                self.state = CameraState.CAPTURING
            
            logger.info("Camera capture started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera capture: {e}")
            self._cleanup_camera_resources()
            
            with self.lock:
                self.state = CameraState.ERROR
            
            # Attempt recovery
            self._attempt_recovery()
            return False
    
    def stop_capture(self):
        """Stop camera capture"""
        logger.info("Stopping camera capture")
        
        with self.lock:
            self.running = False
        
        # Wait for capture thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5.0)
        
        # Cleanup camera resources
        self._cleanup_camera_resources()
        
        with self.lock:
            self.state = CameraState.DISABLED if cv2 is None else CameraState.STOPPED
        
        logger.info("Camera capture stopped")
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.frame.copy()
        return None
    
    def get_buffered_frame(self, max_age: float = 1.0) -> Optional['CameraFrame']:
        """Get a recent frame from buffer"""
        current_time = time.time()
        
        try:
            # Try to get a recent frame from buffer
            while not self.frame_buffer.empty():
                frame = self.frame_buffer.get_nowait()
                if current_time - frame.timestamp <= max_age:
                    return frame
            
            # If no recent frame in buffer, return current frame
            if self.current_frame and current_time - self.current_frame.timestamp <= max_age:
                return self.current_frame
                
        except queue.Empty:
            pass
        
        return None
    
    def capture_photo(self, filename: Optional[str] = None, max_retries: int = 3) -> Optional[str]:
        """Capture a photo with retry logic"""
        if cv2 is None:
            logger.warning("OpenCV not available. Cannot capture photo.")
            return None
        for attempt in range(max_retries):
            try:
                # Get a recent frame
                frame_data = self.get_buffered_frame(max_age=0.5)
                
                if frame_data is None:
                    # Wait a moment and try to get current frame
                    time.sleep(0.1)
                    frame = self.get_current_frame()
                    if frame is None:
                        raise RuntimeError("No frame available for photo capture")
                else:
                    frame = frame_data.frame
                
                # Generate filename if not provided
                if filename is None:
                    timestamp = int(time.time())
                    filename = f"jarvis_photo_{timestamp}.jpg"
                
                # Ensure filename has extension
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filename += '.jpg'
                
                filepath = self.photos_dir / filename
                
                # Save photo
                success = cv2.imwrite(str(filepath), frame)
                
                if not success:
                    raise RuntimeError("Failed to save photo")
                
                # Update statistics
                with self.lock:
                    self.stats['photos_taken'] += 1
                    self.stats['successful_captures'] += 1
                
                logger.info(f"Photo captured successfully: {filepath}")
                return str(filepath)
                
            except Exception as e:
                logger.warning(f"Photo capture attempt {attempt + 1} failed: {e}")
                
                with self.lock:
                    self.stats['failed_captures'] += 1
                
                if attempt < max_retries - 1:
                    time.sleep(0.2)  # Brief delay before retry
                else:
                    logger.error(f"Photo capture failed after {max_retries} attempts")
                    return None
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get camera system status"""
        with self.lock:
            uptime = time.time() - self.stats['uptime_start']
            
            return {
                'state': self.state.value,
                'available': self.state in [CameraState.READY, CameraState.CAPTURING],
                'capturing': self.state == CameraState.CAPTURING,
                'has_frame': self.current_frame is not None,
                'config': {
                    'camera_index': self.config.camera_index,
                    'resolution': (self.config.width, self.config.height),
                    'fps_target': self.config.fps,
                    'fps_actual': self.stats['fps_actual']
                },
                'stats': {
                    **self.stats,
                    'uptime': uptime,
                    'buffer_size': self.frame_buffer.qsize(),
                    'success_rate': (
                        self.stats['successful_captures'] / 
                        max(self.stats['total_frames'], 1)
                    )
                }
            }
    
    def cleanup(self):
        """Cleanup camera resources"""
        self.stop_capture()
        self._cleanup_camera_resources()
    
    def _find_working_camera_config(self) -> bool:
        """Find a working camera configuration"""
        if cv2 is None:
            return False
        logger.debug("Finding working camera configuration")
        
        # Try different camera indices
        for camera_index in self.config.fallback_indices:
            if camera_index == -1:
                # Try to find any available camera
                for i in range(10):  # Check first 10 indices
                    if self._test_camera_index(i):
                        self.config.camera_index = i
                        break
                else:
                    continue
            else:
                if not self._test_camera_index(camera_index):
                    continue
                self.config.camera_index = camera_index
            
            # Try different resolutions
            for width, height in self.config.fallback_resolutions:
                for fps in self.config.fallback_fps:
                    if self._test_camera_settings(camera_index, width, height, fps):
                        self.config.width = width
                        self.config.height = height
                        self.config.fps = fps
                        
                        logger.info(f"Found working camera config: index={camera_index}, "
                                  f"resolution={width}x{height}, fps={fps}")
                        return True
        
        logger.error("No working camera configuration found")
        return False
    
    def _test_camera_index(self, camera_index: int) -> bool:
        """Test if a camera index is available"""
        try:
            test_camera = cv2.VideoCapture(camera_index)
            if test_camera.isOpened():
                ret, frame = test_camera.read()
                test_camera.release()
                return ret and frame is not None
        except Exception:
            pass
        return False
    
    def _test_camera_settings(self, camera_index: int, width: int, height: int, fps: int) -> bool:
        """Test specific camera settings"""
        try:
            test_camera = cv2.VideoCapture(camera_index)
            if not test_camera.isOpened():
                return False
            
            test_camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            test_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            test_camera.set(cv2.CAP_PROP_FPS, fps)
            
            # Test capture
            ret, frame = test_camera.read()
            test_camera.release()
            
            return ret and frame is not None and frame.shape[:2] == (height, width)
            
        except Exception:
            return False
    
    def _test_camera_capture(self) -> bool:
        """Test camera capture functionality"""
        if cv2 is None:
            return False
        try:
            logger.debug("Testing camera capture")
            
            test_camera = cv2.VideoCapture(self.config.camera_index)
            if not test_camera.isOpened():
                return False
            
            test_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            test_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            test_camera.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Capture a few frames to test
            for _ in range(5):
                ret, frame = test_camera.read()
                if not ret or frame is None:
                    test_camera.release()
                    return False
                
                # Check frame properties
                if frame.shape[:2] != (self.config.height, self.config.width):
                    logger.warning(f"Frame size mismatch: expected {self.config.height}x{self.config.width}, "
                                 f"got {frame.shape[0]}x{frame.shape[1]}")
            
            test_camera.release()
            logger.debug("Camera capture test passed")
            return True
            
        except Exception as e:
            logger.error(f"Camera capture test failed: {e}")
            return False
    
    def _capture_loop(self):
        """Main camera capture loop"""
        logger.info("Camera capture loop started")
        
        frame_time = 1.0 / self.config.fps
        last_frame_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Maintain target FPS
                elapsed = current_time - last_frame_time
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                
                # Capture frame
                ret, frame = self.camera.read()
                
                if not ret or frame is None:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.1)
                    continue
                
                # Create frame object
                camera_frame = CameraFrame(
                    frame=frame,
                    timestamp=time.time(),
                    frame_id=self.frame_counter,
                    width=frame.shape[1],
                    height=frame.shape[0]
                )
                
                # Update current frame
                with self.lock:
                    self.current_frame = camera_frame
                    self.frame_counter += 1
                    self.stats['total_frames'] += 1
                
                # Add to buffer (remove old frames if full)
                try:
                    self.frame_buffer.put_nowait(camera_frame)
                except queue.Full:
                    # Remove oldest frame and add new one
                    try:
                        self.frame_buffer.get_nowait()
                        self.frame_buffer.put_nowait(camera_frame)
                    except queue.Empty:
                        pass
                
                # Update FPS calculation
                self.fps_counter += 1
                if self.fps_counter >= 30:  # Update every 30 frames
                    fps_elapsed = time.time() - self.fps_start_time
                    if fps_elapsed > 0:
                        with self.lock:
                            self.stats['fps_actual'] = self.fps_counter / fps_elapsed
                    
                    self.fps_counter = 0
                    self.fps_start_time = time.time()
                
                last_frame_time = time.time()
                
            except Exception as e:
                logger.error(f"Error in camera capture loop: {e}")
                
                # Attempt recovery
                if not self._attempt_recovery():
                    break
                
                time.sleep(1.0)
        
        logger.info("Camera capture loop stopped")
    
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
            
            self.state = CameraState.RECOVERING
        
        logger.info(f"Attempting camera system recovery (attempt {self.recovery_attempts})")
        
        try:
            # Cleanup existing resources
            self._cleanup_camera_resources()
            
            # Wait a moment
            time.sleep(1.0)
            
            # Reinitialize
            if self.initialize():
                with self.lock:
                    self.recovery_attempts = 0
                logger.info("Camera system recovery successful")
                return True
            else:
                raise RuntimeError("Recovery initialization failed")
                
        except Exception as e:
            logger.error(f"Camera system recovery failed: {e}")
            
            with self.lock:
                self.state = CameraState.ERROR
                self.last_error_time = time.time()
            
            return False
    
    def _cleanup_camera_resources(self):
        """Cleanup camera resources"""
        if self.camera:
            try:
                self.camera.release()
            except Exception as e:
                logger.error(f"Error releasing camera: {e}")
            finally:
                self.camera = None
    
    def _delayed_retry_init(self, delay: float):
        """Delayed initialization retry"""
        time.sleep(delay)
        self.initialize()

# Global robust camera manager instance
robust_camera_manager = None

def get_camera_manager() -> 'RobustCameraManager':
    """Get global camera manager instance"""
    global robust_camera_manager
    if robust_camera_manager is None:
        robust_camera_manager = RobustCameraManager()
    return robust_camera_manager
