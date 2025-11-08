"""
Translation Service
Handles English-to-ISL translation using ML model or fallback to rule-based
"""

import os
import re
import torch
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import ML model components
try:
    from ml_pipeline.models.translator import Seq2SeqTranslator
    from ml_pipeline.utils.vocab import Vocabulary
    from ml_pipeline.config import ModelConfig
    ML_MODEL_AVAILABLE = True
except ImportError:
    ML_MODEL_AVAILABLE = False
    logger.warning("ML model components not available")


class TranslationService:
    """Service for English-to-ISL translation"""
    
    def __init__(self):
        self.model = None
        self.src_vocab = None
        self.tgt_vocab = None
        self.config = None
        self.device = "cpu"
        self._model_loaded = False
        self.use_ml_model = False
        
    def load_model_if_available(self) -> bool:
        """
        Load ML translation model if available
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if not ML_MODEL_AVAILABLE:
            logger.info("ML model components not available")
            return False
        
        try:
            # Check if model files exist
            base_dir = Path(__file__).parent.parent
            model_path = base_dir / "models" / "lstm_translator.pth"
            vocab_src_path = base_dir / "models" / "vocab_src.json"
            vocab_tgt_path = base_dir / "models" / "vocab_tgt.json"
            
            if not model_path.exists():
                logger.info(f"Model file not found: {model_path}")
                logger.info("ML translation model not trained yet. Using rule-based translation.")
                return False
            
            if not vocab_src_path.exists() or not vocab_tgt_path.exists():
                logger.warning("Vocabulary files not found. Cannot load ML model.")
                return False
            
            # Load configuration
            self.config = ModelConfig()
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load vocabularies
            logger.info("Loading vocabularies...")
            self.src_vocab = Vocabulary()
            self.tgt_vocab = Vocabulary()
            self.src_vocab.load(str(vocab_src_path))
            self.tgt_vocab.load(str(vocab_tgt_path))
            
            logger.info(f"Source vocab size: {self.src_vocab.size()}")
            logger.info(f"Target vocab size: {self.tgt_vocab.size()}")
            
            # Load model
            logger.info("Loading translation model...")
            self.model = Seq2SeqTranslator(
                src_vocab_size=self.src_vocab.size(),
                tgt_vocab_size=self.tgt_vocab.size(),
                embed_dim=self.config.EMBED_DIM,
                hidden_dim=self.config.HIDDEN_DIM,
                num_layers=self.config.NUM_LAYERS,
                dropout=self.config.DROPOUT
            )
            
            # Load weights
            checkpoint = torch.load(str(model_path), map_location=self.device)
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                elif 'state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['state_dict'])
                else:
                    # Try loading as state dict directly
                    self.model.load_state_dict(checkpoint)
            else:
                # Assume it's a state dict
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            
            self._model_loaded = True
            self.use_ml_model = True
            
            logger.info(f"✅ ML translation model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            logger.info("Falling back to rule-based translation")
            return False
    
    def translate_ml(self, english_text: str) -> List[str]:
        """
        Translate English text to ISL using ML model
        
        Args:
            english_text: English sentence
            
        Returns:
            List of ISL tokens/words
        """
        if not self._model_loaded:
            raise RuntimeError("ML model not loaded")
        
        try:
            # Encode input
            normalized_text = re.sub(r'\s+', ' ', english_text).strip()
            if not normalized_text:
                return []
            src_indices = self.src_vocab.encode(normalized_text, add_special_tokens=True)
            src_tensor = torch.tensor([src_indices], dtype=torch.long).to(self.device)
            
            # Translate
            with torch.no_grad():
                translated_indices = self.model.translate(
                    src_tensor,
                    max_length=self.config.MAX_LENGTH,
                    sos_idx=self.tgt_vocab.word2idx.get('<sos>', 2),
                    eos_idx=self.tgt_vocab.word2idx.get('<eos>', 3)
                )
            
            # Decode output (translated_indices is already a list)
            translated_text = self.tgt_vocab.decode(translated_indices)
            
            # Split into tokens (filter empty strings and special tokens)
            tokens = [t for t in translated_text.split() if t and t not in ['<pad>', '<sos>', '<eos>', '<unk>']]
            
            # If no tokens, return original as fallback
            if not tokens:
                logger.warning(f"ML translation produced no tokens, using original")
                tokens = english_text.split()
            
            logger.info(f"ML Translation: '{english_text}' → '{' '.join(tokens)}'")
            return tokens
            
        except Exception as e:
            logger.error(f"ML translation error: {e}")
            import traceback
            traceback.print_exc()
            raise


# Global instance
_translation_service = None

def get_translation_service() -> TranslationService:
    """Get or create translation service instance"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
        # Try to load ML model
        _translation_service.load_model_if_available()
    return _translation_service

def is_ml_model_available() -> bool:
    """Check if ML translation model is available and loaded"""
    service = get_translation_service()
    return service._model_loaded and service.use_ml_model

