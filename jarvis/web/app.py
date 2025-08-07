"""
JARVIS Web Interface - Flask Backend with WebSocket support
"""

import os
import sys
import base64
import json
import time
import threading
import logging
from io import BytesIO
from typing import Optional, Dict, Any

import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
import eventlet

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from jarvis.core.parallel_manager import get_jarvis_instance
from jarvis.core.reliability_manager import get_reliability_manager
from jarvis.config.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret-key-2025'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global JARVIS instance
jarvis_instance: Optional[JARVISPrototype] = None
camera_thread: Optional[threading.Thread] = None
camera_running = False

class WebJARVIS:
    """Web interface wrapper for JARVIS"""

    def __init__(self):
        self.jarvis = get_jarvis_instance()
        self.reliability_manager = get_reliability_manager()
        self.status = {
            'initialized': False,
            'listening': False,
            'camera_active': False,
            'last_command': '',
            'last_response': '',
            'system_info': {}
        }
        self.initialize_jarvis()
    
    def initialize_jarvis(self):
        """Initialize JARVIS components"""
        try:
            logger.info("Initializing JARVIS for web interface...")

            # Start reliability manager
            self.reliability_manager.start()

            # Initialize JARVIS
            try:
                if not self.jarvis.initialize():
                    logger.warning("JARVIS core initialization failed, using fallback mode")
                    self.status['initialized'] = False
                else:
                    # Start JARVIS
                    if not self.jarvis.start():
                        logger.warning("JARVIS start failed, using fallback mode")
                        self.status['initialized'] = False
                    else:
                        self.status['initialized'] = True
            except Exception as e:
                logger.warning(f"JARVIS initialization error: {e}, using fallback mode")
                self.status['initialized'] = False

            # Update status based on initialization
            if self.status['initialized']:
                self.status['listening'] = True
                self.status['camera_active'] = True
                logger.info("JARVIS web interface initialized successfully")
            else:
                self.status['listening'] = False
                self.status['camera_active'] = False
                logger.info("JARVIS web interface running in fallback mode")

            # Override speech callback to emit to web
            original_callback = self.jarvis._on_speech_detected
            
            def web_speech_callback(audio_data):
                # Emit status update
                socketio.emit('status_update', {
                    'type': 'speech_detected',
                    'message': 'Processing speech...'
                })
                
                # Process speech
                try:
                    transcription = self.jarvis.asr_manager.transcribe(audio_data)
                    if transcription.strip():
                        self.status['last_command'] = transcription
                        
                        # Emit transcription
                        socketio.emit('speech_transcribed', {
                            'text': transcription,
                            'timestamp': time.time()
                        })
                        
                        # Process command
                        response = self.jarvis._process_command(transcription)
                        if response:
                            self.status['last_response'] = response
                            
                            # Emit response
                            socketio.emit('jarvis_response', {
                                'text': response,
                                'timestamp': time.time()
                            })
                            
                            # Speak response
                            self.jarvis.tts_manager.speak(response, play_audio=True)
                            
                except Exception as e:
                    logger.error(f"Error in web speech callback: {e}")
                    socketio.emit('error', {'message': str(e)})
            
            # Replace callback
            if self.jarvis.audio_manager:
                self.jarvis.audio_manager.speech_callback = web_speech_callback
            
            self.status['initialized'] = True
            self.update_system_info()
            
            logger.info("JARVIS web interface initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize JARVIS: {e}")
            self.status['initialized'] = False
    
    def update_system_info(self):
        """Update system information"""
        if not self.jarvis:
            return
        
        try:
            asr_status = self.jarvis.asr_manager.get_status()
            tts_status = self.jarvis.tts_manager.get_status()
            vision_status = self.jarvis.vision_manager.get_vision_status()
            
            self.status['system_info'] = {
                'asr_available': asr_status.get('available', False),
                'tts_available': tts_status.get('available', False),
                'camera_active': vision_status.get('vision_active', False),
                'device': config.device.upper(),
                'photos_taken': vision_status.get('photos_taken', 0)
            }
        except Exception as e:
            logger.error(f"Error updating system info: {e}")
    
    def start_listening(self):
        """Start voice listening"""
        if self.jarvis and not self.status['listening']:
            try:
                self.jarvis.start()
                self.status['listening'] = True
                return True
            except Exception as e:
                logger.error(f"Error starting listening: {e}")
                return False
        return False
    
    def stop_listening(self):
        """Stop voice listening"""
        if self.jarvis and self.status['listening']:
            try:
                self.jarvis.stop()
                self.status['listening'] = False
                return True
            except Exception as e:
                logger.error(f"Error stopping listening: {e}")
                return False
        return False
    
    def process_text_command(self, text: str) -> str:
        """Process text command directly"""
        self.status['last_command'] = text

        if not self.jarvis or not self.status['initialized']:
            # Fallback command processing
            response = self._fallback_command_processing(text)
        else:
            try:
                response = self.jarvis.process_text_command(text)
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                response = f"Error: {str(e)}"

        if response:
            self.status['last_response'] = response
                return response
            return "No response generated"
        except Exception as e:
            logger.error(f"Error processing text command: {e}")
            return f"Error: {str(e)}"

    def _fallback_command_processing(self, command: str) -> str:
        """Basic command processing when JARVIS is not fully initialized"""
        command = command.lower().strip()

        if any(word in command for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm JARVIS, but I'm currently running in limited mode. Some features may not be available."
        elif 'time' in command:
            import datetime
            return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."
        elif 'date' in command:
            import datetime
            return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."
        elif any(word in command for word in ['help', 'what can you do']):
            return "I'm running in limited mode. Try: 'hello', 'what time is it?', 'what's the date?'"
        else:
            return f"I heard: '{command}'. I'm currently in limited mode - full JARVIS features are loading."
    
    def get_camera_frame(self) -> Optional[str]:
        """Get current camera frame as base64 encoded image"""
        if not self.jarvis or not self.jarvis.vision_manager:
            return None
        
        try:
            # Start camera if not active
            if not self.jarvis.vision_manager.is_monitoring:
                self.jarvis.vision_manager.start_vision_system()
                time.sleep(0.5)  # Wait for camera to stabilize
            
            frame = self.jarvis.vision_manager.camera.get_current_frame()
            if frame is not None:
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # Convert to base64
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                return f"data:image/jpeg;base64,{frame_base64}"
            
        except Exception as e:
            logger.error(f"Error getting camera frame: {e}")
        
        return None
    
    def take_photo(self) -> Dict[str, Any]:
        """Take a photo"""
        if not self.jarvis or not self.jarvis.vision_manager:
            return {'success': False, 'message': 'Camera not available'}
        
        try:
            photo_path = self.jarvis.vision_manager.take_photo()
            if photo_path:
                self.update_system_info()
                return {
                    'success': True, 
                    'message': f'Photo saved as {photo_path.split("/")[-1]}',
                    'path': photo_path
                }
            else:
                return {'success': False, 'message': 'Failed to capture photo'}
        except Exception as e:
            logger.error(f"Error taking photo: {e}")
            return {'success': False, 'message': str(e)}

# Global web JARVIS instance
web_jarvis = WebJARVIS()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    web_jarvis.update_system_info()
    return jsonify(web_jarvis.status)

@app.route('/api/command', methods=['POST'])
def process_command():
    """Process text command"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    response = web_jarvis.process_text_command(data['text'])
    return jsonify({'response': response})

@app.route('/api/photo', methods=['POST'])
def take_photo():
    """Take a photo"""
    result = web_jarvis.take_photo()
    return jsonify(result)

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status_update', {
        'type': 'connected',
        'message': 'Connected to JARVIS',
        'status': web_jarvis.status
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('start_listening')
def handle_start_listening():
    """Start voice listening"""
    success = web_jarvis.start_listening()
    emit('status_update', {
        'type': 'listening_started' if success else 'error',
        'message': 'Voice listening started' if success else 'Failed to start listening'
    })

@socketio.on('stop_listening')
def handle_stop_listening():
    """Stop voice listening"""
    success = web_jarvis.stop_listening()
    emit('status_update', {
        'type': 'listening_stopped' if success else 'error',
        'message': 'Voice listening stopped' if success else 'Failed to stop listening'
    })

@socketio.on('text_command')
def handle_text_command(data):
    """Handle text command via WebSocket"""
    if 'text' not in data:
        emit('error', {'message': 'No text provided'})
        return
    
    response = web_jarvis.process_text_command(data['text'])
    emit('jarvis_response', {
        'text': response,
        'timestamp': time.time()
    })

@socketio.on('request_camera_frame')
def handle_camera_frame_request():
    """Send camera frame to client"""
    frame_data = web_jarvis.get_camera_frame()
    if frame_data:
        emit('camera_frame', {'image': frame_data})
    else:
        emit('camera_frame', {'image': None})

def camera_stream_thread():
    """Background thread for camera streaming"""
    global camera_running
    
    while camera_running:
        try:
            frame_data = web_jarvis.get_camera_frame()
            if frame_data:
                socketio.emit('camera_frame', {'image': frame_data})
            
            eventlet.sleep(1/15)  # 15 FPS
            
        except Exception as e:
            logger.error(f"Error in camera stream: {e}")
            eventlet.sleep(1)

if __name__ == '__main__':
    # Start camera streaming thread
    camera_running = True
    camera_thread = threading.Thread(target=camera_stream_thread, daemon=True)
    camera_thread.start()
    
    # Run the app
    logger.info("Starting JARVIS Web Interface...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
