"""
JARVIS AI Assistant Configuration
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AudioConfig:
    """Audio processing configuration"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    format: str = "int16"
    
    # Voice Activity Detection
    vad_threshold: float = 0.005  # Even lower threshold for better sensitivity
    silence_duration: float = 1.0  # seconds of silence before stopping recording
    min_recording_duration: float = 0.5  # minimum recording duration
    
    # Audio file paths
    temp_audio_dir: str = "jarvis/temp_audio"

@dataclass
class ASRConfig:
    """Automatic Speech Recognition configuration"""
    model_name: str = "nvidia/stt_en_conformer_ctc_large"  # NeMo ASR model
    language: str = "en"
    
    # Model cache directory
    cache_dir: str = "jarvis/models/asr"

@dataclass
class TTSConfig:
    """Text-to-Speech configuration"""
    model_name: str = "nvidia/tts_en_fastpitch"  # NeMo TTS model
    vocoder_name: str = "nvidia/tts_hifigan"     # Vocoder for audio generation
    language: str = "en"
    
    # Voice settings
    speaking_rate: float = 1.0
    pitch: float = 0.0
    
    # Model cache directory
    cache_dir: str = "jarvis/models/tts"

@dataclass
class VisionConfig:
    """Computer vision configuration"""
    camera_index: int = 0  # Confirmed working index from test
    resolution: tuple = (640, 480)
    fps: int = 30
    
    # Model settings
    model_name: str = "nvidia/neva-22b"  # NeMo multimodal model
    cache_dir: str = "jarvis/models/vision"

@dataclass
class ConversationConfig:
    """AI conversation configuration"""
    # Language model settings
    model_type: str = "openai"  # "openai", "local", "huggingface"
    model_name: str = "gpt-4"
    api_key: Optional[str] = None
    
    # Local model settings (if using local LLM)
    local_model_path: Optional[str] = None
    
    # Conversation settings
    max_history: int = 10
    system_prompt: str = """You are JARVIS, an advanced AI assistant. You are helpful, intelligent, and have a personality similar to the AI assistant from Iron Man. You can:
- Process voice commands and respond naturally
- Analyze visual input from cameras
- Help with coding and VS Code workspace management
- Provide technical assistance and general conversation

Keep responses concise but informative. Use a professional yet friendly tone."""

@dataclass
class MCPConfig:
    """Model Context Protocol configuration for VS Code integration"""
    server_port: int = 8000
    server_host: str = "localhost"
    
    # VS Code workspace settings
    workspace_path: Optional[str] = None
    allowed_file_extensions: list = None
    
    def __post_init__(self):
        if self.allowed_file_extensions is None:
            self.allowed_file_extensions = ['.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt']

@dataclass
class JARVISConfig:
    """Main JARVIS configuration"""
    # Component configurations
    audio: AudioConfig = None
    asr: ASRConfig = None
    tts: TTSConfig = None
    vision: VisionConfig = None
    conversation: ConversationConfig = None
    mcp: MCPConfig = None
    
    # System settings
    debug: bool = True
    log_level: str = "INFO"
    
    # Device settings
    device: str = "cuda"  # "cuda" or "cpu"
    
    def __post_init__(self):
        """Initialize configuration after creation"""
        # Initialize component configs if not provided
        if self.audio is None:
            self.audio = AudioConfig()
        if self.asr is None:
            self.asr = ASRConfig()
        if self.tts is None:
            self.tts = TTSConfig()
        if self.vision is None:
            self.vision = VisionConfig()
        if self.conversation is None:
            self.conversation = ConversationConfig()
        if self.mcp is None:
            self.mcp = MCPConfig()

        # Create necessary directories
        os.makedirs(self.audio.temp_audio_dir, exist_ok=True)
        os.makedirs(self.asr.cache_dir, exist_ok=True)
        os.makedirs(self.tts.cache_dir, exist_ok=True)
        os.makedirs(self.vision.cache_dir, exist_ok=True)

        # Load environment variables
        if not self.conversation.api_key and self.conversation.model_type == "openai":
            self.conversation.api_key = os.getenv("OPENAI_API_KEY")

        # Set workspace path if not provided
        if not self.mcp.workspace_path:
            self.mcp.workspace_path = os.getcwd()

# Global configuration instance
config = JARVISConfig()

def load_config(config_file: Optional[str] = None) -> JARVISConfig:
    """Load configuration from file or environment"""
    if config_file and os.path.exists(config_file):
        # TODO: Implement config file loading (JSON/YAML)
        pass
    
    return config

def update_config(**kwargs) -> None:
    """Update configuration values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
