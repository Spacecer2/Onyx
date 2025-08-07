#!/usr/bin/env python3
"""
JARVIS AI Assistant Prototype
Phase 1: Basic Speech-to-Text and Text-to-Speech Pipeline
"""

import logging
import time
import threading
import signal
import sys
import os
from typing import Optional

# Add the parent directory to the path so we can import jarvis modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis.config.config import config
from jarvis.audio.asr import ASRManager
from jarvis.audio.tts import TTSManager
from jarvis.audio.audio_io import AudioManager
from jarvis.vision.camera import VisionManager
from jarvis.vision.analysis import VisionAnalysisManager
from jarvis.audio.sounds import (play_startup, play_shutdown, play_success,
                                play_error, play_camera_click, play_thinking)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JARVISPrototype:
    """JARVIS AI Assistant Prototype - Phase 1"""
    
    def __init__(self):
        self.running = False
        self.asr_manager = None
        self.tts_manager = None
        self.audio_manager = None
        self.vision_manager = None
        self.vision_analyzer = None

        # Initialize components
        self._initialize_components()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_components(self):
        """Initialize all JARVIS components"""
        try:
            logger.info("Initializing JARVIS components...")
            
            # Initialize ASR
            logger.info("Loading ASR (Speech-to-Text) system...")
            self.asr_manager = ASRManager()
            
            # Initialize TTS
            logger.info("Loading TTS (Text-to-Speech) system...")
            self.tts_manager = TTSManager()
            
            # Initialize Audio I/O
            logger.info("Setting up audio input/output...")
            self.audio_manager = AudioManager(speech_callback=self._on_speech_detected)

            # Initialize Vision System
            logger.info("Setting up vision system...")
            self.vision_manager = VisionManager()
            self.vision_analyzer = VisionAnalysisManager()

            logger.info("JARVIS components initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize JARVIS components: {e}")
            raise
    
    def _on_speech_detected(self, audio_data):
        """Callback when speech is detected and recorded"""
        try:
            # Immediate feedback - voice detected
            print("🎤 Voice detected! Processing...")

            # Save audio for debugging (optional)
            if config.debug:
                temp_file = os.path.join(config.audio.temp_audio_dir,
                                       f"input_{int(time.time())}.wav")
                self.audio_manager.recorder.save_recording_to_file(audio_data, temp_file)
                logger.debug(f"Audio saved to {temp_file}")

            # Transcribe speech to text
            print("🧠 Transcribing speech...")
            play_thinking()  # Audio feedback for thinking
            transcription = self.asr_manager.transcribe(audio_data)

            if transcription.strip():
                print(f"📝 You said: '{transcription}'")

                # Process the transcription
                print("💭 Thinking...")
                response = self._process_command(transcription)

                if response:
                    print(f"🗣️ JARVIS: '{response}'")
                    print("🔊 Speaking...")

                    # Convert response to speech
                    self.tts_manager.speak(response, play_audio=True)
                    play_success()  # Audio feedback for successful response
                    print("✅ Response complete!")
                else:
                    print("❌ No response generated")
                    play_error()  # Audio feedback for no response
            else:
                print("❌ Could not understand speech")
                play_error()  # Audio feedback for transcription failure

        except Exception as e:
            print(f"❌ Error processing speech: {e}")
            play_error()  # Audio feedback for error
            logger.error(f"Error processing speech: {e}")
    
    def _process_command(self, text: str) -> Optional[str]:
        """Process transcribed text and generate response"""
        text = text.lower().strip()
        
        # Enhanced command processing with better matching
        logger.info(f"Processing command: '{text}'")

        if any(word in text for word in ["hello", "hi", "hey", "jarvis"]):
            return "Hello! I'm JARVIS, your AI assistant. How can I help you today?"
        
        elif "how are you" in text:
            return "I'm functioning optimally, thank you for asking. All systems are online."
        
        elif "what time" in text or "time is it" in text:
            current_time = time.strftime("%I:%M %p")
            return f"The current time is {current_time}."
        
        elif "weather" in text:
            return "I don't have access to weather data yet, but I'm working on it. This feature will be available in a future update."
        
        elif any(word in text for word in ["camera", "vision", "see", "photo", "picture", "capture", "look"]):
            return self._handle_vision_command(text)
        
        elif "code" in text or "vs code" in text:
            return "VS Code integration is planned for Phase 4. I'll be able to help with your coding projects soon."
        
        elif "stop" in text or "quit" in text or "exit" in text:
            self.stop()
            return "Goodbye! JARVIS is shutting down."
        
        elif "status" in text or "system" in text:
            return self._get_system_status()
        
        elif "test" in text:
            return "Test successful! Speech recognition and text-to-speech are working properly."
        
        else:
            # Default response for unrecognized commands
            responses = [
                "I heard you say: " + text + ". I'm still learning, so I might not understand everything yet.",
                "That's interesting. I'm a prototype, so my responses are limited right now.",
                "I'm processing what you said: " + text + ". More capabilities are coming soon!",
                "I understand you're talking about: " + text + ". Let me know if you need help with something specific."
            ]
            
            import random
            return random.choice(responses)

    def _handle_vision_command(self, text: str) -> str:
        """Handle vision-related commands"""
        text = text.lower()

        try:
            # Start camera if not already active
            if not self.vision_manager.is_monitoring:
                print("📷 Starting camera system...")
                if not self.vision_manager.start_vision_system():
                    return "I'm sorry, I couldn't access the camera. Please check if a camera is connected."

            if "take photo" in text or "take picture" in text or "capture" in text:
                play_camera_click()  # Camera shutter sound
                photo_path = self.vision_manager.take_photo()
                if photo_path:
                    play_success()  # Success sound
                    return f"Photo captured successfully! I saved it as {photo_path.split('/')[-1]}."
                else:
                    play_error()  # Error sound
                    return "I couldn't take a photo right now. Please try again."

            elif "what do you see" in text or "describe" in text or "look" in text:
                frame = self.vision_manager.camera.get_current_frame()
                if frame is not None:
                    description = self.vision_analyzer.analyze_current_view(frame)
                    return f"Looking at the camera feed: {description}"
                else:
                    return "I can't see anything right now. The camera might not be working properly."

            elif "stop camera" in text or "close camera" in text:
                self.vision_manager.stop_vision_system()
                return "Camera system stopped."

            else:
                # General camera/vision query
                if self.vision_manager.is_monitoring:
                    status = self.vision_manager.get_vision_status()
                    camera_info = status['camera']
                    return f"Camera system is active. Resolution: {camera_info['actual_resolution']}, Photos taken: {status['photos_taken']}. Try saying 'what do you see' or 'take a photo'."
                else:
                    return "Camera system is not active. Say 'start camera' or 'what do you see' to begin."

        except Exception as e:
            logger.error(f"Error handling vision command: {e}")
            return "I encountered an error with the camera system. Please try again."
    
    def _get_system_status(self) -> str:
        """Get system status information"""
        asr_status = self.asr_manager.get_status()
        tts_status = self.tts_manager.get_status()
        audio_status = self.audio_manager.get_status()
        vision_status = self.vision_manager.get_vision_status()

        status_parts = [
            f"ASR system: {'Online' if asr_status['available'] else 'Offline'}",
            f"TTS system: {'Online' if tts_status['available'] else 'Offline'}",
            f"Audio recording: {'Active' if audio_status['recording'] else 'Inactive'}",
            f"Camera system: {'Active' if vision_status['vision_active'] else 'Inactive'}",
            f"Running on: {config.device.upper()}"
        ]

        return "System status: " + ", ".join(status_parts)
    
    def start(self):
        """Start JARVIS"""
        if self.running:
            return
        
        logger.info("Starting JARVIS AI Assistant...")
        self.running = True
        
        # Start audio recording
        self.audio_manager.start_listening()
        
        # Welcome message
        print("\n" + "="*60)
        print("🤖 JARVIS AI Assistant is now ONLINE!")
        print("="*60)
        print("🎤 Listening for voice commands...")
        print("💡 Try saying: 'Hello JARVIS', 'What time is it?', 'What do you see?'")
        print("📷 Vision commands: 'Take a photo', 'What do you see?', 'Start camera'")
        print("🛑 Say 'Stop' or 'Quit' to exit")
        print("="*60)

        welcome_msg = "JARVIS AI Assistant is now online. I'm listening for your voice commands."
        logger.info(welcome_msg)

        # Play startup sound
        play_startup()
        time.sleep(0.5)  # Brief pause after startup sound

        self.tts_manager.speak(welcome_msg, play_audio=True)

        print("🔊 Welcome message played. Ready for voice input!")
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop JARVIS"""
        if not self.running:
            return
        
        logger.info("Stopping JARVIS...")
        self.running = False
        
        # Stop audio recording
        if self.audio_manager:
            self.audio_manager.stop_listening()

        # Stop vision system
        if self.vision_manager:
            self.vision_manager.stop_vision_system()

        # Play shutdown sound
        play_shutdown()

        logger.info("JARVIS stopped")

    def run(self):
        """Run JARVIS (start and keep running)"""
        self.start()

        try:
            # Keep running until stopped
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

def main():
    """Main entry point"""
    print("=" * 60)
    print("🤖 JARVIS AI Assistant - Prototype Phase 1")
    print("=" * 60)
    print("Features in this prototype:")
    print("✓ Speech-to-Text (ASR) using NeMo")
    print("✓ Text-to-Speech (TTS) using NeMo")
    print("✓ Real-time voice activity detection")
    print("✓ Basic command processing")
    print()
    print("Try saying:")
    print("• 'Hello JARVIS'")
    print("• 'What time is it?'")
    print("• 'How are you?'")
    print("• 'System status'")
    print("• 'Stop' or 'Quit' to exit")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        # Create and start JARVIS
        jarvis = JARVISPrototype()
        jarvis.start()
        
    except Exception as e:
        logger.error(f"Failed to start JARVIS: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
