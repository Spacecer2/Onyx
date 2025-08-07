#!/usr/bin/env python3
"""
JARVIS Robust AI Assistant - Production-ready system with parallel processing,
advanced capabilities, and comprehensive reliability management
"""

import sys
import time
import signal
import logging
import threading
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('jarvis/logs/jarvis_robust.log')
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal")
    if 'jarvis_system' in globals():
        jarvis_system.stop()
    sys.exit(0)

class RobustJARVISSystem:
    """Complete JARVIS system with all advanced capabilities"""
    
    def __init__(self):
        self.running = False
        self.start_time = time.time()
        
        # Import core components
        from jarvis.core.parallel_manager import get_jarvis_instance
        from jarvis.core.task_queue import task_queue
        from jarvis.core.reliability_manager import get_reliability_manager
        from jarvis.audio.sounds import play_startup, play_shutdown
        
        # Initialize components
        self.jarvis = get_jarvis_instance()
        self.task_queue = task_queue
        self.reliability_manager = get_reliability_manager()
        self.play_startup = play_startup
        self.play_shutdown = play_shutdown
        
        # Register components with reliability manager
        self._register_components()
        
        logger.info("RobustJARVISSystem initialized")
    
    def _register_components(self):
        """Register all components with reliability manager"""
        # Register core components
        self.reliability_manager.register_component(
            "audio_manager", 
            lambda: self.jarvis.audio_manager._attempt_recovery()
        )
        
        self.reliability_manager.register_component(
            "camera_manager",
            lambda: self.jarvis.camera_manager._attempt_recovery()
        )
        
        self.reliability_manager.register_component(
            "task_queue",
            lambda: self._restart_task_queue()
        )
        
        self.reliability_manager.register_component("asr_manager")
        self.reliability_manager.register_component("tts_manager")
    
    def start(self) -> bool:
        """Start the complete JARVIS system"""
        logger.info("🚀 Starting JARVIS Robust AI Assistant...")
        print("=" * 80)
        print("🤖 JARVIS ROBUST AI ASSISTANT")
        print("=" * 80)
        print("🔧 Initializing advanced parallel processing system...")
        
        try:
            # Start reliability manager
            self.reliability_manager.start()
            
            # Play startup sound
            try:
                self.play_startup()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Startup sound failed: {e}")
            
            # Initialize JARVIS core
            print("🧠 Loading AI models and speech systems...")
            if not self.jarvis.initialize():
                logger.error("Failed to initialize JARVIS core")
                return False
            
            # Start JARVIS
            print("🎤 Starting voice recognition and camera systems...")
            if not self.jarvis.start():
                logger.error("Failed to start JARVIS")
                return False
            
            self.running = True
            
            # Display system status
            self._display_startup_status()
            
            logger.info("JARVIS Robust system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start JARVIS system: {e}")
            return False
    
    def stop(self):
        """Stop the JARVIS system gracefully"""
        if not self.running:
            return
        
        logger.info("🛑 Stopping JARVIS Robust AI Assistant...")
        print("\n" + "=" * 80)
        print("🛑 SHUTTING DOWN JARVIS...")
        print("=" * 80)
        
        self.running = False
        
        try:
            # Play shutdown sound
            try:
                self.play_shutdown()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Shutdown sound failed: {e}")
            
            # Stop JARVIS core
            print("🔧 Stopping core systems...")
            self.jarvis.stop()
            
            # Stop reliability manager
            print("📊 Saving system health reports...")
            self.reliability_manager.stop()
            
            uptime = time.time() - self.start_time
            print(f"✅ JARVIS stopped gracefully after {uptime:.1f} seconds")
            print("👋 Goodbye!")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def run(self):
        """Run JARVIS in interactive mode"""
        if not self.start():
            return False
        
        try:
            # Main loop
            while self.running:
                time.sleep(1)
                
                # Check system health periodically
                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    self._check_system_health()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()
        
        return True
    
    def _display_startup_status(self):
        """Display system startup status"""
        status = self.jarvis.get_system_status()
        
        print("\n📊 SYSTEM STATUS:")
        print(f"   🎤 Audio System: {'✅ READY' if status.audio_available else '❌ OFFLINE'}")
        print(f"   📷 Camera System: {'✅ READY' if status.camera_available else '❌ OFFLINE'}")
        print(f"   🧠 Speech Recognition: {'✅ READY' if status.asr_available else '❌ OFFLINE'}")
        print(f"   🗣️ Text-to-Speech: {'✅ READY' if status.tts_available else '❌ OFFLINE'}")
        
        print("\n🎯 AVAILABLE CAPABILITIES:")
        print("   🗣️ Voice Commands - Say 'Hello JARVIS' to start")
        print("   💬 Text Chat - Type commands in web interface")
        print("   📷 Camera Control - 'Take a photo', 'What do you see?'")
        print("   🌐 Web Search - 'Search for [topic]'")
        print("   📚 Wikipedia - 'Tell me about [topic]'")
        print("   🌤️ Weather - 'What's the weather?'")
        print("   📰 News - 'Tell me the news'")
        print("   😄 Entertainment - 'Tell me a joke'")
        print("   💻 System Control - 'System info', 'Open [app]'")
        print("   🧮 Calculations - 'Calculate 2 + 2'")
        print("   ⏰ Time & Date - 'What time is it?'")
        
        print("\n🌐 WEB INTERFACE:")
        print("   Launch with: python launch_jarvis_web.py")
        print("   URL: http://localhost:5000")
        
        print("\n🎮 VOICE COMMANDS:")
        print("   - 'Hello JARVIS' - Start conversation")
        print("   - 'What can you do?' - List capabilities")
        print("   - 'Help' - Get assistance")
        print("   - 'Stop' or 'Quit' - Exit system")
        
        print("\n" + "=" * 80)
        print("🎙️ JARVIS IS NOW LISTENING...")
        print("🔊 Listen for audio feedback on each action")
        print("💡 Try saying: 'Hello JARVIS, what can you do?'")
        print("=" * 80)
    
    def _check_system_health(self):
        """Check and report system health"""
        try:
            health = self.reliability_manager.get_system_health()
            
            # Report component health to reliability manager
            status = self.jarvis.get_system_status()
            
            from jarvis.core.reliability_manager import HealthStatus
            
            # Report audio health
            audio_status = HealthStatus.HEALTHY if status.audio_available else HealthStatus.WARNING
            self.reliability_manager.report_component_health("audio_manager", audio_status)
            
            # Report camera health
            camera_status = HealthStatus.HEALTHY if status.camera_available else HealthStatus.WARNING
            self.reliability_manager.report_component_health("camera_manager", camera_status)
            
            # Report task queue health
            queue_stats = self.task_queue.get_queue_stats()
            queue_status = HealthStatus.HEALTHY if queue_stats['queue_size'] < 100 else HealthStatus.WARNING
            self.reliability_manager.report_component_health("task_queue", queue_status, queue_stats)
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
    
    def _restart_task_queue(self) -> bool:
        """Restart task queue (recovery callback)"""
        try:
            self.task_queue.stop()
            time.sleep(1)
            self.task_queue.start()
            return True
        except Exception as e:
            logger.error(f"Failed to restart task queue: {e}")
            return False

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run JARVIS system
    global jarvis_system
    jarvis_system = RobustJARVISSystem()
    
    try:
        success = jarvis_system.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
