#!/usr/bin/env python3
"""
Launch JARVIS Web Interface
"""

import os
import sys
import webbrowser
import time
import threading

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    """Main function to launch JARVIS web interface"""
    print("🚀 Starting JARVIS Web Interface...")
    print("=" * 60)
    
    try:
        # Import the web app
        from jarvis.web.app import app, socketio
        
        print("🌐 Web server starting on http://localhost:5000")
        print("📱 Opening browser automatically...")
        print("🎤 Voice commands and camera will be available in the web interface")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Open browser in background thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start the web server
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down JARVIS Web Interface...")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        return False
    
    print("✅ JARVIS Web Interface stopped. Goodbye!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
