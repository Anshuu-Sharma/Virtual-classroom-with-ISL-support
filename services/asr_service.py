"""
Whisper ASR Service for Speech Recognition
Uses OpenAI Whisper base model for accurate speech-to-text conversion
"""

import whisper
import torch
import os
import logging
from typing import Optional, Dict
import tempfile

logger = logging.getLogger(__name__)

class ASRService:
    """Automatic Speech Recognition service using Whisper"""
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        """
        Initialize Whisper ASR service
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
                       Default: 'base' for balance of accuracy and speed
            device: Device to run on ('cpu', 'cuda', or None for auto-detect)
        """
        self.model_size = model_size
        self.model = None
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model_loaded = False
        
    def load_model(self):
        """Lazy load model to reduce startup time"""
        if not self._model_loaded:
            try:
                logger.info(f"Loading Whisper {self.model_size} model on {self.device}...")
                self.model = whisper.load_model(self.model_size, device=self.device)
                self._model_loaded = True
                logger.info(f"Whisper model loaded successfully on {self.device}")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {str(e)}")
                raise
    
    def transcribe(self, audio_file_path: str, language: str = "en") -> Dict[str, any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language code (default: 'en' for English)
            
        Returns:
            Dictionary with transcription results:
            {
                'text': str,  # Transcribed text
                'language': str,  # Detected language
                'segments': list  # Timestamped segments
            }
        """
        if not self._model_loaded:
            self.load_model()
        
        try:
            logger.info(f"Transcribing audio file: {audio_file_path}")
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Try to load and transcribe
            # Use fp16=False for CPU compatibility and better error handling
            result = self.model.transcribe(
                audio_file_path,
                language=language,
                task="transcribe",
                fp16=False,  # Use FP32 for CPU compatibility
                verbose=False  # Reduce output
            )
            
            return {
                'text': result['text'].strip(),
                'language': result.get('language', language),
                'segments': result.get('segments', [])
            }
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Transcription failed: {error_msg}")
            
            # Check if it's an ffmpeg-related error
            if 'ffmpeg' in error_msg.lower() or 'file not found' in error_msg.lower() or 'cannot find the file' in error_msg.lower():
                raise RuntimeError(
                    "FFmpeg is required for audio processing. "
                    "Please install ffmpeg or use Web Speech API as fallback. "
                    f"Original error: {error_msg}"
                )
            raise
    
    def transcribe_bytes(self, audio_bytes: bytes, language: str = "en") -> Dict[str, any]:
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Audio file as bytes
            language: Language code
            
        Returns:
            Dictionary with transcription results
        """
        # Save to temporary file - try webm first (common from MediaRecorder)
        # Whisper can handle webm directly
        tmp_path = None
        try:
            # Try webm first (common format from browser MediaRecorder)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            # Try transcribing with webm
            try:
                result = self.transcribe(tmp_path, language)
                return result
            except Exception as e:
                logger.warning(f"WebM transcription failed: {e}, trying WAV format")
                # If webm fails, try saving as wav
                os.unlink(tmp_path)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name
                result = self.transcribe(tmp_path, language)
                return result
        finally:
            # Clean up temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    def is_available(self) -> bool:
        """Check if Whisper service is available"""
        try:
            if not self._model_loaded:
                self.load_model()
            return self.model is not None
        except:
            return False


# Global instance (singleton pattern)
_asr_service_instance = None

def get_asr_service(model_size: str = "base", device: Optional[str] = None) -> ASRService:
    """Get or create ASR service instance (singleton)"""
    global _asr_service_instance
    if _asr_service_instance is None:
        _asr_service_instance = ASRService(model_size=model_size, device=device)
    return _asr_service_instance

