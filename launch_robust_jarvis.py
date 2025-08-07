#!/usr/bin/env python3
"""
Launch JARVIS Robust AI Assistant with all advanced capabilities
"""

import os
import sys
import argparse
import webbrowser
import time
import threading
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def create_directories():
    """Create necessary directories"""
    directories = [
        "jarvis/logs",
        "jarvis/photos",
        "jarvis/temp",
        "jarvis/web/static/sounds"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        ('torch', 'torch'),
        ('nemo_toolkit', 'nemo'),
        ('cv2', 'cv2'),
        ('numpy', 'numpy'),
        ('pyaudio', 'pyaudio'),
        ('flask', 'flask'),
        ('flask_socketio', 'flask_socketio'),
        ('eventlet', 'eventlet'),
        ('wikipedia', 'wikipedia'),
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),
        ('psutil', 'psutil'),
        ('pyjokes', 'pyjokes')
    ]

    missing = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            # Try alternative imports
            if import_name == 'wikipedia':
                try:
                    import wikipediaapi
                    continue
                except ImportError:
                    pass
            missing.append(package_name)

    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install them with:")
        print("pip install torch nemo_toolkit opencv-python numpy pyaudio flask flask-socketio eventlet wikipedia-api requests beautifulsoup4 psutil pyjokes")
        return False

    return True

def launch_terminal_mode():
    """Launch JARVIS in terminal mode"""
    print("🚀 Launching JARVIS in Terminal Mode...")
    
    try:
        from jarvis_robust import main
        main()
    except KeyboardInterrupt:
        print("\n👋 JARVIS terminated by user")
    except Exception as e:
        print(f"❌ Error launching JARVIS: {e}")

def launch_web_mode():
    """Launch JARVIS in web interface mode"""
    print("🌐 Launching JARVIS Web Interface...")
    
    def open_browser():
        time.sleep(3)  # Wait for server to start
        webbrowser.open('http://localhost:5000')
    
    # Start browser opener in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        from jarvis.web.app import app, socketio
        print("🌐 Starting web server on http://localhost:5000")
        print("📱 Browser will open automatically...")
        print("🛑 Press Ctrl+C to stop")
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Web interface terminated by user")
    except Exception as e:
        print(f"❌ Error launching web interface: {e}")

def run_tests():
    """Run comprehensive test suite"""
    print("🧪 Running JARVIS Test Suite...")
    
    try:
        from test_robust_jarvis import main
        return main()
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def show_system_info():
    """Show system information and capabilities"""
    print("🤖 JARVIS ROBUST AI ASSISTANT")
    print("=" * 80)
    print("🎯 ADVANCED CAPABILITIES:")
    print("   🗣️ Voice Recognition & Synthesis (NVIDIA NeMo)")
    print("   📷 Computer Vision & Photo Capture")
    print("   🌐 Web Search & Information Retrieval")
    print("   📚 Wikipedia Integration")
    print("   🌤️ Weather Information")
    print("   📰 News Headlines")
    print("   😄 Entertainment (Jokes)")
    print("   💻 System Control & Information")
    print("   🧮 Mathematical Calculations")
    print("   ⏰ Time & Date Services")
    print("   🔧 Parallel Processing Architecture")
    print("   📊 Reliability & Health Monitoring")
    print("   🌐 Beautiful Web Interface")
    
    print("\n🎮 USAGE MODES:")
    print("   Terminal Mode: python launch_robust_jarvis.py --terminal")
    print("   Web Interface: python launch_robust_jarvis.py --web")
    print("   Run Tests: python launch_robust_jarvis.py --test")
    
    print("\n🎤 VOICE COMMANDS:")
    print("   - 'Hello JARVIS' - Start conversation")
    print("   - 'What time is it?' - Get current time")
    print("   - 'What's the weather?' - Weather information")
    print("   - 'Search for [topic]' - Web search")
    print("   - 'Tell me about [topic]' - Wikipedia lookup")
    print("   - 'Tell me the news' - Latest headlines")
    print("   - 'Tell me a joke' - Entertainment")
    print("   - 'Take a photo' - Camera capture")
    print("   - 'What do you see?' - Visual analysis")
    print("   - 'System info' - Computer status")
    print("   - 'Calculate [expression]' - Math")
    print("   - 'Open [application]' - Launch apps")
    print("   - 'Help' - Get assistance")
    print("   - 'Stop' or 'Quit' - Exit")
    
    print("\n🔧 SYSTEM REQUIREMENTS:")
    print("   - Python 3.8+")
    print("   - CUDA-capable GPU (recommended)")
    print("   - Microphone for voice input")
    print("   - Camera for vision features")
    print("   - Internet connection for web features")
    
    print("=" * 80)

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(
        description="JARVIS Robust AI Assistant Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_robust_jarvis.py --terminal    # Terminal mode
  python launch_robust_jarvis.py --web         # Web interface
  python launch_robust_jarvis.py --test        # Run tests
  python launch_robust_jarvis.py --info        # Show info
        """
    )
    
    parser.add_argument('--terminal', action='store_true',
                       help='Launch in terminal mode')
    parser.add_argument('--web', action='store_true',
                       help='Launch web interface')
    parser.add_argument('--test', action='store_true',
                       help='Run test suite')
    parser.add_argument('--info', action='store_true',
                       help='Show system information')
    parser.add_argument('--skip-deps', action='store_true',
                       help='Skip dependency check')
    
    args = parser.parse_args()
    
    # Show info if requested
    if args.info:
        show_system_info()
        return
    
    # Create necessary directories
    create_directories()
    
    # Check dependencies unless skipped
    if not args.skip_deps:
        print("🔍 Checking dependencies...")
        if not check_dependencies():
            return
        print("✅ All dependencies found!")
    
    # Determine mode
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    elif args.web:
        launch_web_mode()
    elif args.terminal:
        launch_terminal_mode()
    else:
        # Default: show options
        print("🤖 JARVIS ROBUST AI ASSISTANT LAUNCHER")
        print("=" * 50)
        print("Please choose a launch mode:")
        print("  --terminal    Terminal interface")
        print("  --web         Web interface (recommended)")
        print("  --test        Run test suite")
        print("  --info        Show system information")
        print("\nExample: python launch_robust_jarvis.py --web")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Launcher interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error in launcher: {e}")
        sys.exit(1)
