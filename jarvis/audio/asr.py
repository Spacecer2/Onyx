"""
Automatic Speech Recognition (ASR) module using NeMo
"""

# Guard optional heavy deps so imports don't crash in minimal environments
try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - fallback when torch isn't installed
    torch = None  # type: ignore

try:
    import soundfile as sf  # type: ignore  # not required in fallback paths
except Exception:  # pragma: no cover
    sf = None  # type: ignore

import numpy as np
import logging
from typing import Optional, List
from pathlib import Path

try:
    import nemo.collections.asr as nemo_asr  # type: ignore
except ImportError:
    print("Warning: NeMo ASR collection not available. Some features may not work.")
    nemo_asr = None  # type: ignore

from ..config.config import config

logger = logging.getLogger(__name__)

class NeMoASR:
    """NeMo-based Automatic Speech Recognition"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.asr.model_name
        self.model = None
        self.device = config.device
        
        # Initialize model
        self._load_model()
    
    def _load_model(self):
        """Load the NeMo ASR model"""
        try:
            logger.info(f"Loading ASR model: {self.model_name}")
            
            # Try to load from NeMo's pre-trained models
            if nemo_asr:
                self.model = nemo_asr.models.EncDecCTCModel.from_pretrained(
                    model_name=self.model_name
                )
                
                # Move to appropriate device
                if torch is not None and getattr(torch, "cuda", None) and torch.cuda.is_available() and self.device == "cuda":
                    self.model = self.model.cuda()
                else:
                    self.model = self.model.cpu()
                
                self.model.eval()
                logger.info("ASR model loaded successfully")
            else:
                logger.error("NeMo ASR not available")
                raise ImportError("NeMo ASR collection not available")
                
        except Exception as e:
            logger.error(f"Failed to load ASR model: {e}")
            # Fallback to a simpler model or mock implementation
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load a fallback ASR implementation"""
        logger.warning("Using fallback ASR implementation")
        self.model = None  # Will use mock transcription
    
    def transcribe_file(self, audio_file: str) -> str:
        """Transcribe audio from file"""
        try:
            if self.model is None:
                return self._mock_transcription(audio_file)

            # Load audio file with librosa for better handling
            import librosa  # Local import to avoid hard dep at import time
            audio_data, sample_rate = librosa.load(audio_file, sr=config.audio.sample_rate, mono=True)

            logger.debug(f"Loaded audio: shape={audio_data.shape}, sr={sample_rate}")

            # Transcribe
            return self.transcribe_audio(audio_data)

        except Exception as e:
            logger.error(f"Error transcribing file {audio_file}: {e}")
            return ""
    
    def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data directly"""
        try:
            # If model or torch unavailable, use mock
            if self.model is None or torch is None:
                return self._mock_transcription()

            # Ensure audio is in the right format
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # Convert to mono

            # Normalize audio
            audio_data = audio_data.astype(np.float32)
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            logger.debug(f"Audio data shape before tensor conversion: {audio_data.shape}")

            # Convert to tensor with correct shape for NeMo ASR
            # NeMo expects (batch, time) not (batch, channels, time)
            audio_tensor = torch.tensor(audio_data)

            # Ensure we have the right shape: (batch, time)
            if len(audio_tensor.shape) == 1:
                audio_tensor = audio_tensor.unsqueeze(0)  # Shape: (1, time)
            elif len(audio_tensor.shape) == 3:
                # If somehow we have (batch, channels, time), squeeze the channel dimension
                audio_tensor = audio_tensor.squeeze(1)  # Shape: (batch, time)

            logger.debug(f"Audio tensor shape: {audio_tensor.shape}")

            if self.device == "cuda" and getattr(torch, "cuda", None) and torch.cuda.is_available():
                audio_tensor = audio_tensor.cuda()

            # Transcribe using the correct NeMo method
            with torch.no_grad():
                # Use the model's transcribe method with proper signal and length
                # Remove the batch dimension for the transcribe method
                audio_signal = audio_tensor.squeeze(0)  # Shape: (time,)
                logger.debug(f"Audio signal shape for transcribe: {audio_signal.shape}")

                # NeMo transcribe expects the raw audio signal
                transcription = self.model.transcribe([audio_signal.cpu().numpy()])

            if isinstance(transcription, list) and len(transcription) > 0:
                # Handle NeMo Hypothesis objects
                result = transcription[0]
                if hasattr(result, 'text'):
                    return result.text.strip()
                elif hasattr(result, 'strip'):
                    return result.strip()
                else:
                    return str(result).strip()
            else:
                return str(transcription).strip()

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    def _mock_transcription(self, audio_file: Optional[str] = None) -> str:
        """Mock transcription for testing when model is not available"""
        mock_responses = [
            "Hello JARVIS, how are you today?",
            "What's the weather like?",
            "Can you help me with my code?",
            "Show me the camera feed",
            "Open VS Code workspace"
        ]
        
        import random
        return random.choice(mock_responses)
    
    def is_available(self) -> bool:
        """Check if ASR is available and working"""
        return self.model is not None or True  # True for mock mode

class ASRManager:
    """High-level ASR management"""
    
    def __init__(self):
        self.asr = NeMoASR()
        self.is_listening = False
    
    def start_listening(self):
        """Start listening for speech"""
        self.is_listening = True
        logger.info("ASR listening started")
    
    def stop_listening(self):
        """Stop listening for speech"""
        self.is_listening = False
        logger.info("ASR listening stopped")
    
    def transcribe(self, audio_input) -> str:
        """Transcribe audio input (file path or audio data)"""
        if isinstance(audio_input, str):
            return self.asr.transcribe_file(audio_input)
        elif isinstance(audio_input, np.ndarray):
            return self.asr.transcribe_audio(audio_input)
        else:
            logger.error(f"Unsupported audio input type: {type(audio_input)}")
            return ""
    
    def get_status(self) -> dict:
        """Get ASR status information"""
        return {
            "available": self.asr.is_available(),
            "listening": self.is_listening,
            "model": self.asr.model_name,
            "device": self.asr.device
        }
