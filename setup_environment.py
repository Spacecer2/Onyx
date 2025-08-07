#!/usr/bin/env python3
"""
JARVIS Environment Setup and Troubleshooting Script
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"🔧 {title}")
    print("=" * 80)

def run_command(command, description="", check=True):
    """Run a command and handle errors"""
    if description:
        print(f"📋 {description}")
    
    print(f"💻 Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ Stderr: {e.stderr}")
        return False, e.stderr

def check_system_requirements():
    """Check system requirements"""
    print_header("SYSTEM REQUIREMENTS CHECK")
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")
    
    # Check OS
    os_name = platform.system()
    print(f"💻 Operating System: {os_name}")
    
    # Check available commands
    commands = ['pip', 'git', 'ffmpeg']
    for cmd in commands:
        if shutil.which(cmd):
            print(f"✅ {cmd} available")
        else:
            print(f"⚠️ {cmd} not found (may be optional)")
    
    return True

def create_directories():
    """Create necessary directories"""
    print_header("CREATING DIRECTORIES")
    
    directories = [
        "jarvis/logs",
        "jarvis/photos", 
        "jarvis/temp",
        "jarvis/models",
        "jarvis/web/static/sounds",
        "jarvis/web/static/css",
        "jarvis/web/static/js"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created: {directory}")
    
    print("✅ All directories created")

def fix_environment():
    """Fix common environment issues"""
    print_header("FIXING ENVIRONMENT ISSUES")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️ Not in virtual environment. Creating one...")
        
        # Create virtual environment
        success, _ = run_command("python -m venv jarvis_env", "Creating virtual environment")
        if success:
            print("✅ Virtual environment created")
            print("🔄 Please activate it with: source jarvis_env/bin/activate")
            return False
        else:
            print("❌ Failed to create virtual environment")
            return False
    else:
        print("✅ Virtual environment detected")
    
    # Upgrade pip
    run_command("pip install --upgrade pip", "Upgrading pip", check=False)
    
    return True

def install_dependencies():
    """Install all required dependencies"""
    print_header("INSTALLING DEPENDENCIES")
    
    # Core dependencies
    core_deps = [
        "torch",
        "numpy",
        "opencv-python",
        "pyaudio",
        "flask",
        "flask-socketio",
        "eventlet",
        "requests",
        "beautifulsoup4",
        "psutil",
        "pyjokes",
        "wikipedia-api",
        "openai",
        "python-dotenv"
    ]
    
    print("📦 Installing core dependencies...")
    for dep in core_deps:
        success, _ = run_command(f"pip install {dep}", f"Installing {dep}", check=False)
        if success:
            print(f"✅ {dep} installed")
        else:
            print(f"⚠️ {dep} installation failed (may already be installed)")
    
    # Try to install NeMo
    print("\n🧠 Installing NVIDIA NeMo...")
    nemo_commands = [
        "pip install nemo_toolkit[all]",
        "pip install nemo_toolkit",
        "pip install git+https://github.com/NVIDIA/NeMo.git"
    ]
    
    nemo_installed = False
    for cmd in nemo_commands:
        print(f"🔄 Trying: {cmd}")
        success, _ = run_command(cmd, check=False)
        if success:
            nemo_installed = True
            print("✅ NeMo installed successfully")
            break
        else:
            print("⚠️ Command failed, trying next...")
    
    if not nemo_installed:
        print("❌ NeMo installation failed. JARVIS will run in limited mode.")
    
    return True

def test_imports():
    """Test if all imports work"""
    print_header("TESTING IMPORTS")
    
    test_modules = [
        ("torch", "PyTorch"),
        ("numpy", "NumPy"),
        ("cv2", "OpenCV"),
        ("flask", "Flask"),
        ("requests", "Requests"),
        ("bs4", "BeautifulSoup"),
        ("psutil", "PSUtil"),
        ("pyjokes", "PyJokes"),
        ("wikipedia", "Wikipedia"),
        ("openai", "OpenAI")
    ]
    
    failed_imports = []
    
    for module, name in test_modules:
        try:
            __import__(module)
            print(f"✅ {name} import OK")
        except ImportError as e:
            print(f"❌ {name} import failed: {e}")
            failed_imports.append(name)
    
    # Test NeMo separately
    try:
        import NeMo
        print("✅ NVIDIA NeMo import OK")
    except ImportError as e:
        print(f"⚠️ NVIDIA NeMo import failed: {e}")
        print("   JARVIS will run in limited mode without advanced speech features")
        failed_imports.append("NeMo")
    
    # Test PyAudio separately (often problematic)
    try:
        import pyaudio
        print("✅ PyAudio import OK")
    except ImportError as e:
        print(f"⚠️ PyAudio import failed: {e}")
        print("   Voice features may not work. Install with: sudo apt-get install portaudio19-dev")
        failed_imports.append("PyAudio")
    
    if failed_imports:
        print(f"\n⚠️ Failed imports: {', '.join(failed_imports)}")
        print("JARVIS will run in limited mode for missing components")
    else:
        print("\n✅ All imports successful!")
    
    return len(failed_imports) == 0

def create_environment_file():
    """Create .env file for configuration"""
    print_header("CREATING ENVIRONMENT CONFIGURATION")
    
    env_content = """# JARVIS Environment Configuration

# OpenAI API Key (for advanced conversations)
OPENAI_API_KEY=your_openai_api_key_here

# Weather API Key (OpenWeatherMap)
OPENWEATHER_API_KEY=your_weather_api_key_here

# News API Key
NEWS_API_KEY=your_news_api_key_here

# JARVIS Configuration
JARVIS_NAME=JARVIS
JARVIS_VOICE_ENABLED=true
JARVIS_CAMERA_ENABLED=true
JARVIS_WEB_ENABLED=true

# Audio Configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024
VAD_THRESHOLD=0.01

# Camera Configuration
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=30

# Web Interface Configuration
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=false

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=jarvis/logs/jarvis.log
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        print("📝 Please edit .env file to add your API keys")
    else:
        print("✅ .env file already exists")
    
    return True

def create_simple_launcher():
    """Create a simple, reliable launcher"""
    print_header("CREATING SIMPLE LAUNCHER")
    
    launcher_content = '''#!/usr/bin/env python3
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
        
        print("🌐 Server starting on http://localhost:5000")
        print("📱 Browser will open automatically...")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50)
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\\n👋 JARVIS stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
'''
    
    with open("jarvis_simple_launcher.py", 'w') as f:
        f.write(launcher_content)
    
    # Make executable
    os.chmod("jarvis_simple_launcher.py", 0o755)
    
    print("✅ Simple launcher created: jarvis_simple_launcher.py")
    return True

def main():
    """Main setup function"""
    print("🚀 JARVIS ENVIRONMENT SETUP AND TROUBLESHOOTING")
    print("=" * 80)
    print("This script will set up and fix your JARVIS environment")
    
    steps = [
        ("System Requirements", check_system_requirements),
        ("Directory Creation", create_directories),
        ("Environment Fix", fix_environment),
        ("Dependencies Installation", install_dependencies),
        ("Import Testing", test_imports),
        ("Environment Configuration", create_environment_file),
        ("Simple Launcher Creation", create_simple_launcher)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        try:
            print(f"\n🔄 Starting: {step_name}")
            result = step_func()
            results.append((step_name, result))
            
            if result:
                print(f"✅ {step_name}: SUCCESS")
            else:
                print(f"⚠️ {step_name}: COMPLETED WITH WARNINGS")
                
        except Exception as e:
            print(f"❌ {step_name}: FAILED - {e}")
            results.append((step_name, False))
    
    # Summary
    print_header("SETUP SUMMARY")
    
    success_count = 0
    for step_name, result in results:
        status = "✅ SUCCESS" if result else "⚠️ WARNING"
        print(f"   {step_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 Overall: {success_count}/{len(results)} steps successful")
    
    if success_count >= len(results) - 1:  # Allow 1 failure
        print("\n🎉 JARVIS ENVIRONMENT SETUP COMPLETE!")
        print("\n🚀 Quick Start Options:")
        print("   1. Simple Mode: python jarvis_simple_launcher.py")
        print("   2. Full Mode: python launch_robust_jarvis.py --web --skip-deps")
        print("   3. Test Mode: python test_robust_jarvis.py")
        
        print("\n📝 Next Steps:")
        print("   1. Edit .env file to add your API keys")
        print("   2. Test the simple launcher first")
        print("   3. If working, try the full system")
        
    else:
        print("\n⚠️ Setup completed with issues. Check the warnings above.")
        print("JARVIS may run in limited mode.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
