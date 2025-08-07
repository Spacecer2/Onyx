#!/usr/bin/env python3
"""
Simple JARVIS launcher - bypasses complex initialization for quick testing
"""

import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def open_browser():
    """Open browser after delay"""
    time.sleep(3)
    webbrowser.open('http://localhost:5000')

def main():
    """Simple main function"""
    print("🚀 JARVIS Simple Launcher")
    print("=" * 50)
    
    # Create directories
    os.makedirs("jarvis/logs", exist_ok=True)
    os.makedirs("jarvis/photos", exist_ok=True)
    
    try:
        print("🌐 Starting JARVIS Web Interface...")
        
        # Start browser opener
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Import and run web app
        from jarvis.web.app import app, socketio
        
        print("🌐 Web server starting on http://localhost:5000")
        print("📱 Browser will open automatically...")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50)
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 JARVIS stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTry running with dependencies check skipped:")
        print("python launch_robust_jarvis.py --web --skip-deps")

if __name__ == "__main__":
    main()
