**Welcome to the Onyx Project**

JARVIS (Onyx) is a modular AI assistant featuring voice (ASR/TTS), computer vision, a web UI, and parallel task orchestration. It is engineered to run even in constrained environments by gracefully degrading when optional dependencies or hardware are unavailable.

What you can do here quickly:
- Run the web UI without heavy ML dependencies
- Exercise the command processing pipeline (mock ASR/TTS)
- Capture photos if OpenCV and a camera are available
- Inspect robust parallel and reliability managers

Quick start (this environment):
- Python packages cannot be installed system-wide. If you need extra deps, create a venv: `python3 -m venv .venv` (install `python3-venv` if needed) then `./.venv/bin/pip install -r requirements.txt`.
- Launch simple web UI: `python3 start_jarvis_simple.py`
- Run basic component test: `python3 test_jarvis_basic.py`

Feature highlights:
- Parallel processing with priority task queue (`jarvis/core/task_queue.py`)
- Reliability manager with health tracking (`jarvis/core/reliability_manager.py`)
- Camera and audio managers with retry/degradation (`jarvis/core/camera_manager.py`, `jarvis/core/audio_manager.py`)
- NeMo-based ASR/TTS with automatic mock fallback (`jarvis/audio/asr.py`, `jarvis/audio/tts.py`)
- Flask + Socket.IO web interface (`jarvis/web/app.py`)

Notes on dependencies:
- If `torch`, `nemo_toolkit`, `pyaudio`, or `opencv-python` are missing, the system uses mock or disabled modes so imports/tests still run.
- To enable full functionality, install dependencies from `requirements.txt` in a virtual environment with audio/camera hardware.

Testing:
- Basic tests: `python3 test_jarvis_basic.py`
- Robust suite: `python3 test_robust_jarvis.py` (works best with optional deps installed)
- Camera tests: `python3 test_camera.py` (requires OpenCV and a camera)
