#!/usr/bin/env python3
"""
JARVIS Simple Launcher - Reliable startup script
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def check_basic_imports():
    """Check basic imports"""
    try:
        import flask
        import requests
        return True
    except ImportError as e:
        print(f"❌ Missing basic dependencies: {e}")
        print("Run: pip install flask requests")
        return False

def open_browser():
    """Open browser after delay"""
    time.sleep(3)
    try:
        webbrowser.open('http://localhost:5000')
        print("🌐 Browser opened")
    except Exception as e:
        print(f"⚠️ Could not open browser: {e}")

def main():
    """Main launcher"""
    print("🚀 JARVIS Simple Launcher")
    print("=" * 50)
    
    if not check_basic_imports():
        return
    
    # Create directories
    os.makedirs("jarvis/logs", exist_ok=True)
    os.makedirs("jarvis/photos", exist_ok=True)
    
    try:
        print("🌐 Starting JARVIS Web Interface...")
        
        # Start browser opener
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Simple Flask app
        from flask import Flask, render_template, request, jsonify
        from flask_socketio import SocketIO
        
        app = Flask(__name__, template_folder='jarvis/web/templates', static_folder='jarvis/web/static')
        app.config['SECRET_KEY'] = 'jarvis-secret-key'
        socketio = SocketIO(app, cors_allowed_origins="*")
        
        @app.route('/')
        def index():
            # Check if enhanced interface exists
            enhanced_template = os.path.join(app.template_folder, 'index_enhanced.html')
            if os.path.exists(enhanced_template):
                return render_template('index_enhanced.html')
            else:
                return render_template('index.html')
        
        @app.route('/api/status')
        def status():
            return jsonify({
                'status': 'running',
                'mode': 'simple',
                'message': 'JARVIS Simple Mode Active'
            })
        
        @app.route('/api/command', methods=['POST'])
        def command():
            data = request.get_json()
            text = data.get('text', '')
            
            # Simple command processing
            response = f"Simple mode response to: {text}"
            if 'hello' in text.lower():
                response = "Hello! I'm JARVIS running in simple mode."
            elif 'time' in text.lower():
                import datetime
                response = f"The time is {datetime.datetime.now().strftime('%I:%M %p')}"
            
            return jsonify({'response': response})

        # Enhanced SocketIO events
        @socketio.on('message')
        def handle_message(data):
            text = data.get('text', '')
            print(f"📝 Received: {text}")

            # Simple response logic
            response = f"I received: {text}"
            if 'hello' in text.lower():
                response = "Hello! I'm JARVIS, your AI assistant. How can I help you today?"
            elif 'time' in text.lower():
                import datetime
                response = f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}"
            elif 'weather' in text.lower():
                response = "I'd be happy to check the weather, but I need weather API integration for that."

            socketio.emit('response', {'response': response})

        @socketio.on('get_status')
        def handle_status():
            socketio.emit('status_update', {
                'audio_available': True,
                'camera_available': True,
                'ai_available': True,
                'overall_status': 'Online'
            })

        @socketio.on('start_camera')
        def handle_start_camera():
            print("📷 Camera feed requested")

        @socketio.on('start_listening')
        def handle_start_listening():
            print("🎤 Voice listening started")

        @socketio.on('stop_listening')
        def handle_stop_listening():
            print("🎤 Voice listening stopped")

        @socketio.on('take_photo')
        def handle_take_photo():
            print("📸 Photo capture requested")

        print("🌐 Server starting on http://localhost:5000")
        print("📱 Browser will open automatically...")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50)
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 JARVIS stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
