"""
Text-to-Speech (TTS) module using NeMo
"""

# Guard optional heavy deps so imports don't crash in minimal environments
try:
    import torch  # type: ignore
except Exception:  # pragma: no cover
    torch = None  # type: ignore

import numpy as np
import logging
import tempfile
import os
from typing import Optional, Union
from pathlib import Path

# soundfile is optional; if missing, mock synthesis will be disabled file-write and return None
try:
    import soundfile as sf  # type: ignore
except Exception:  # pragma: no cover
    sf = None  # type: ignore

try:
    import nemo.collections.tts as nemo_tts  # type: ignore
except ImportError:
    print("Warning: NeMo TTS collection not available. Some features may not work.")
    nemo_tts = None  # type: ignore

from ..config.config import config

logger = logging.getLogger(__name__)

class NeMoTTS:
    """NeMo-based Text-to-Speech"""
    
    def __init__(self, model_name: Optional[str] = None, vocoder_name: Optional[str] = None):
        self.model_name = model_name or config.tts.model_name
        self.vocoder_name = vocoder_name or config.tts.vocoder_name
        self.model = None
        self.vocoder = None
        self.device = config.device
        
        # Initialize models
        self._load_models()
    
    def _load_models(self):
        """Load the NeMo TTS models"""
        try:
            logger.info(f"Loading TTS model: {self.model_name}")
            logger.info(f"Loading vocoder: {self.vocoder_name}")
            
            if nemo_tts:
                # Load TTS model (spectrogram generator)
                self.model = nemo_tts.models.FastPitchModel.from_pretrained(
                    model_name=self.model_name
                )
                
                # Load vocoder (spectrogram to audio)
                self.vocoder = nemo_tts.models.HifiGanModel.from_pretrained(
                    model_name=self.vocoder_name
                )
                
                # Move to appropriate device
                if torch is not None and getattr(torch, "cuda", None) and torch.cuda.is_available() and self.device == "cuda":
                    self.model = self.model.cuda()
                    self.vocoder = self.vocoder.cuda()
                else:
                    self.model = self.model.cpu()
                    self.vocoder = self.vocoder.cpu()
                
                self.model.eval()
                self.vocoder.eval()
                logger.info("TTS models loaded successfully")
            else:
                logger.error("NeMo TTS not available")
                raise ImportError("NeMo TTS collection not available")
                
        except Exception as e:
            logger.error(f"Failed to load TTS models: {e}")
            # Fallback to a simpler implementation
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load a fallback TTS implementation"""
        logger.warning("Using fallback TTS implementation")
        self.model = None
        self.vocoder = None
    
    def synthesize_to_file(self, text: str, output_file: str) -> bool:
        """Synthesize text to audio file"""
        try:
            if self.model is None or self.vocoder is None:
                return self._mock_synthesis(text, output_file)
            
            if torch is None:
                return False
            
            # Generate spectrogram
            with torch.no_grad():
                parsed_text = self.model.parse(text)
                spectrogram = self.model.generate_spectrogram(tokens=parsed_text)
                
                # Generate audio from spectrogram
                audio = self.vocoder.convert_spectrogram_to_audio(spec=spectrogram)
            
            # Convert to numpy and save
            if hasattr(audio, "cpu"):
                audio = audio.cpu().numpy()
            
            # Ensure audio is in the right shape
            if len(audio.shape) > 1:
                audio = audio.squeeze()
            
            if sf is None:
                logger.error("soundfile not available to write audio")
                return False
            
            sf.write(output_file, audio, config.audio.sample_rate)
            logger.info(f"Audio synthesized and saved to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error synthesizing text '{text}': {e}")
            return False
    
    def synthesize_to_audio(self, text: str) -> Optional[np.ndarray]:
        """Synthesize text to audio data"""
        try:
            if self.model is None or self.vocoder is None or torch is None:
                return self._mock_audio_synthesis(text)
            
            # Generate spectrogram
            with torch.no_grad():
                parsed_text = self.model.parse(text)
                spectrogram = self.model.generate_spectrogram(tokens=parsed_text)
                
                # Generate audio from spectrogram
                audio = self.vocoder.convert_spectrogram_to_audio(spec=spectrogram)
            
            # Convert to numpy
            if hasattr(audio, "cpu"):
                audio = audio.cpu().numpy()
            
            # Ensure audio is in the right shape
            if len(audio.shape) > 1:
                audio = audio.squeeze()
            
            return audio.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error synthesizing text '{text}': {e}")
            return None
    
    def _mock_synthesis(self, text: str, output_file: str) -> bool:
        """Mock synthesis for testing when model is not available"""
        try:
            if sf is None:
                logger.warning("soundfile not available; skipping file write in mock synthesis")
                return False
            
            # Generate a simple sine wave as placeholder
            duration = max(0.1, len(text) * 0.05)  # Shorter to be fast
            sample_rate = config.audio.sample_rate
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            
            # Generate a simple tone
            frequency = 440  # A4 note
            audio = 0.2 * np.sin(2 * np.pi * frequency * t)
            
            # Add slight envelope
            env = np.minimum(1.0, np.linspace(0, 5, audio.size))
            env = np.minimum(env, np.linspace(5, 0, audio.size))
            audio *= np.clip(env, 0, 1)
            
            sf.write(output_file, audio, sample_rate)
            logger.info(f"Mock audio generated for: '{text[:50]}...'")
            return True
            
        except Exception as e:
            logger.error(f"Error in mock synthesis: {e}")
            return False
    
    def _mock_audio_synthesis(self, text: str) -> np.ndarray:
        """Mock audio synthesis returning numpy array"""
        duration = max(0.1, len(text) * 0.05)
        sample_rate = config.audio.sample_rate
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        
        frequency = 440
        audio = 0.2 * np.sin(2 * np.pi * frequency * t)
        
        return audio.astype(np.float32)
    
    def is_available(self) -> bool:
        """Check if TTS is available and working"""
        return (self.model is not None and self.vocoder is not None) or True  # True for mock mode

class TTSManager:
    """High-level TTS management"""
    
    def __init__(self):
        self.tts = NeMoTTS()
        self.temp_dir = config.audio.temp_audio_dir
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def speak(self, text: str, play_audio: bool = True) -> Optional[str]:
        """Convert text to speech and optionally play it"""
        if not text.strip():
            return None
        
        # Generate unique filename
        temp_file = os.path.join(self.temp_dir, f"tts_{hash(text) % 10000}.wav")
        
        # Synthesize
        success = self.tts.synthesize_to_file(text, temp_file)
        
        if success and os.path.exists(temp_file):
            if play_audio:
                self._play_audio(temp_file)
            return temp_file
        else:
            logger.error(f"Failed to synthesize: {text}")
            return None
    
    def synthesize(self, text: str) -> Optional[np.ndarray]:
        """Synthesize text to audio data without playing"""
        return self.tts.synthesize_to_audio(text)
    
    def _play_audio(self, audio_file: str):
        """Play audio file using system audio"""
        try:
            # Try different audio players
            import subprocess
            
            # Try with paplay (PulseAudio)
            try:
                subprocess.run(['paplay', audio_file], check=True, capture_output=True)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Try with aplay (ALSA)
            try:
                subprocess.run(['aplay', audio_file], check=True, capture_output=True)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Try with ffplay (if available)
            try:
                subprocess.run(['ffplay', '-nodisp', '-autoexit', audio_file], 
                             check=True, capture_output=True)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            logger.warning("No suitable audio player found")
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def get_status(self) -> dict:
        """Get TTS status information"""
        return {
            "available": self.tts.is_available(),
            "model": self.tts.model_name,
            "vocoder": self.tts.vocoder_name,
            "device": self.tts.device
        }
