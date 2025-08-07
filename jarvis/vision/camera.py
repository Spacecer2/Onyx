"""
Camera system for JARVIS AI Assistant
"""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Optional, Callable, Tuple
from pathlib import Path
import os

from ..config.config import config

logger = logging.getLogger(__name__)

class CameraManager:
    """Manages camera access and video capture"""
    
    def __init__(self, camera_index: Optional[int] = None):
        self.camera_index = camera_index or config.vision.camera_index
        self.resolution = config.vision.resolution
        self.fps = config.vision.fps
        
        self.cap = None
        self.is_active = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        
        # Callbacks
        self.frame_callback = None
        
        # Statistics
        self.frames_captured = 0
        self.last_frame_time = 0
        
    def initialize_camera(self) -> bool:
        """Initialize the camera"""
        try:
            logger.info(f"Initializing camera {self.camera_index}")
            
            # Try to open the camera
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Test capture
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to capture test frame")
                self.cap.release()
                return False
            
            logger.info(f"Camera initialized: {frame.shape[1]}x{frame.shape[0]} @ {self.fps}fps")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def start_capture(self, frame_callback: Optional[Callable] = None):
        """Start continuous frame capture"""
        if self.is_active:
            logger.warning("Camera capture already active")
            return
        
        if not self.cap or not self.cap.isOpened():
            if not self.initialize_camera():
                logger.error("Cannot start capture - camera not initialized")
                return
        
        self.frame_callback = frame_callback
        self.is_active = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        logger.info("Camera capture started")
    
    def stop_capture(self):
        """Stop frame capture"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info("Camera capture stopped")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        logger.debug("Camera capture loop started")
        
        while self.is_active:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.1)
                    continue
                
                # Update statistics
                self.frames_captured += 1
                self.last_frame_time = time.time()
                
                # Store current frame
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Call callback if provided
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        logger.error(f"Error in frame callback: {e}")
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
        
        logger.debug("Camera capture loop ended")
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def capture_photo(self, filename: Optional[str] = None) -> Optional[str]:
        """Capture a single photo"""
        # Wait a moment for camera to stabilize if just started
        if self.frames_captured < 5:
            import time
            time.sleep(0.5)

        frame = self.get_current_frame()

        if frame is None:
            logger.error("No frame available for photo capture")
            return None
        
        if filename is None:
            timestamp = int(time.time())
            filename = f"jarvis_photo_{timestamp}.jpg"
        
        # Ensure photos directory exists
        photos_dir = Path("jarvis/photos")
        photos_dir.mkdir(exist_ok=True)
        
        filepath = photos_dir / filename
        
        try:
            cv2.imwrite(str(filepath), frame)
            logger.info(f"Photo saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            return None
    
    def get_camera_info(self) -> dict:
        """Get camera information and statistics"""
        info = {
            "camera_index": self.camera_index,
            "resolution": self.resolution,
            "fps": self.fps,
            "is_active": self.is_active,
            "frames_captured": self.frames_captured,
            "has_current_frame": self.current_frame is not None
        }
        
        if self.cap and self.cap.isOpened():
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            info.update({
                "actual_resolution": (actual_width, actual_height),
                "actual_fps": actual_fps,
                "backend": self.cap.getBackendName()
            })
        
        return info
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_capture()

class VisionManager:
    """High-level vision system management"""
    
    def __init__(self):
        self.camera = CameraManager()
        self.is_monitoring = False
        
        # Create directories
        os.makedirs("jarvis/photos", exist_ok=True)
        os.makedirs("jarvis/vision_temp", exist_ok=True)
    
    def start_vision_system(self):
        """Start the complete vision system"""
        print("📷 Starting camera system...")
        
        if not self.camera.initialize_camera():
            print("❌ Failed to initialize camera")
            return False
        
        self.camera.start_capture(frame_callback=self._on_frame_captured)
        self.is_monitoring = True
        
        print("✅ Camera system active!")
        return True
    
    def stop_vision_system(self):
        """Stop the vision system"""
        print("📷 Stopping camera system...")
        self.camera.stop_capture()
        self.is_monitoring = False
        print("✅ Camera system stopped")
    
    def _on_frame_captured(self, frame):
        """Callback for each captured frame"""
        # This could be used for real-time analysis
        pass
    
    def take_photo(self, description: str = "") -> Optional[str]:
        """Take a photo with optional description"""
        if not self.is_monitoring:
            print("❌ Camera not active")
            return None
        
        print("📸 Taking photo...")
        
        timestamp = int(time.time())
        filename = f"photo_{timestamp}.jpg"
        
        filepath = self.camera.capture_photo(filename)
        
        if filepath:
            print(f"✅ Photo saved: {filepath}")
            return filepath
        else:
            print("❌ Failed to take photo")
            return None
    
    def get_vision_status(self) -> dict:
        """Get comprehensive vision system status"""
        camera_info = self.camera.get_camera_info()
        
        return {
            "vision_active": self.is_monitoring,
            "camera": camera_info,
            "photos_taken": len(list(Path("jarvis/photos").glob("*.jpg"))) if Path("jarvis/photos").exists() else 0
        }
    
    def describe_current_view(self) -> str:
        """Get a description of what the camera currently sees"""
        if not self.is_monitoring:
            return "Camera is not active"
        
        frame = self.camera.get_current_frame()
        if frame is None:
            return "No image available from camera"
        
        # Basic image analysis
        height, width = frame.shape[:2]
        
        # Calculate brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        # Detect if image is mostly dark or bright
        if brightness < 50:
            lighting = "very dark"
        elif brightness < 100:
            lighting = "dark"
        elif brightness < 150:
            lighting = "moderately lit"
        elif brightness < 200:
            lighting = "bright"
        else:
            lighting = "very bright"
        
        # Basic color analysis
        b, g, r = cv2.split(frame)
        dominant_color = "unknown"
        
        avg_b, avg_g, avg_r = np.mean(b), np.mean(g), np.mean(r)
        
        if avg_r > avg_g and avg_r > avg_b:
            dominant_color = "reddish"
        elif avg_g > avg_r and avg_g > avg_b:
            dominant_color = "greenish"
        elif avg_b > avg_r and avg_b > avg_g:
            dominant_color = "bluish"
        else:
            dominant_color = "neutral colored"
        
        description = f"I can see a {lighting} scene that appears {dominant_color}. The image is {width}x{height} pixels."
        
        return description
