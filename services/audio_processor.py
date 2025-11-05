"""
Audio Processing Utilities
Handles audio format conversion, validation, and preprocessing
"""

import os
import logging
import subprocess
import tempfile
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio preprocessing and validation utilities"""
    
    # Supported audio formats
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm', '.mp4'}
    
    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate audio file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > AudioProcessor.MAX_FILE_SIZE:
            return False, f"File too large ({file_size / 1024 / 1024:.2f}MB). Max: 50MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Check extension
        ext = Path(file_path).suffix.lower()
        if ext not in AudioProcessor.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {ext}. Supported: {', '.join(AudioProcessor.SUPPORTED_FORMATS)}"
        
        return True, None
    
    @staticmethod
    def convert_to_wav(input_path: str, output_path: Optional[str] = None, 
                      sample_rate: int = 16000, channels: int = 1) -> str:
        """
        Convert audio file to WAV format using ffmpeg
        
        Args:
            input_path: Input audio file path
            output_path: Output WAV file path (optional, creates temp file if None)
            sample_rate: Target sample rate (default: 16000 for Whisper)
            channels: Number of channels (1 = mono, 2 = stereo)
            
        Returns:
            Path to converted WAV file
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.wav')
        
        try:
            # Use ffmpeg to convert
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ar', str(sample_rate),  # Sample rate
                '-ac', str(channels),     # Channels
                '-y',                     # Overwrite output
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            logger.info(f"Converted {input_path} to {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")
            raise RuntimeError(f"Audio conversion failed: {e.stderr.decode()}")
        except FileNotFoundError:
            logger.warning("FFmpeg not found. Attempting direct processing...")
            # If ffmpeg not available, return original path
            # Whisper can handle many formats directly
            return input_path
    
    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """
        Get audio file information
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        try:
            # Try using ffprobe if available
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            import json
            info = json.loads(result.stdout)
            return info
            
        except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
            # Fallback: basic file info
            file_size = os.path.getsize(file_path)
            return {
                'format': {
                    'size': str(file_size),
                    'filename': os.path.basename(file_path)
                }
            }

