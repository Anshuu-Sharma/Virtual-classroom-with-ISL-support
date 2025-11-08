"""
Vocabulary Management
Handles vocabulary creation and tokenization
"""

import logging
from typing import Dict, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class Vocabulary:
    """Vocabulary class for managing word-to-index mappings"""
    
    def __init__(self):
        self.word2idx = {
            '<pad>': 0,
            '<unk>': 1,
            '<sos>': 2,
            '<eos>': 3
        }
        self.idx2word = {0: '<pad>', 1: '<unk>', 2: '<sos>', 3: '<eos>'}
        self.word_counts = Counter()
    
    def add_word(self, word: str):
        """Add word to vocabulary"""
        if word not in self.word2idx:
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word
    
    def add_words_from_text(self, text: str):
        """Add words from text to vocabulary"""
        words = text.lower().split()
        for word in words:
            self.word_counts[word] += 1
    
    def build_vocab(self, texts: List[str], min_freq: int = 2):
        """
        Build vocabulary from list of texts
        
        Args:
            texts: List of text strings
            min_freq: Minimum frequency for word to be included
        """
        # Count word frequencies
        for text in texts:
            self.add_words_from_text(text)
        
        # Add words above min frequency
        for word, count in self.word_counts.items():
            if count >= min_freq:
                self.add_word(word)
        
        logger.info(f"Built vocabulary with {len(self.word2idx)} words")
    
    def encode(self, text: str, max_length: int = None, add_special_tokens: bool = False) -> List[int]:
        """
        Encode text to sequence of indices
        
        Args:
            text: Input text
            max_length: Maximum sequence length (pad or truncate)
            add_special_tokens: Ensure <sos>/<eos> tokens are present
            
        Returns:
            List of word indices
        """
        words = text.lower().split()

        if add_special_tokens:
            if not words or words[0] != '<sos>':
                words = ['<sos>'] + words
            if not words or words[-1] != '<eos>':
                words = words + ['<eos>']
        indices = [self.word2idx.get(word, self.word2idx['<unk>']) for word in words]
        
        if max_length:
            if len(indices) > max_length:
                indices = indices[:max_length]
            else:
                indices = indices + [self.word2idx['<pad>']] * (max_length - len(indices))
        
        return indices
    
    def decode(self, indices: List[int]) -> str:
        """
        Decode sequence of indices to text
        
        Args:
            indices: List of word indices
            
        Returns:
            Decoded text string
        """
        words = [self.idx2word.get(idx, '<unk>') for idx in indices]
        # Remove special tokens for final output
        words = [w for w in words if w not in ['<pad>', '<sos>', '<eos>']]
        return ' '.join(words)
    
    def size(self) -> int:
        """Get vocabulary size"""
        return len(self.word2idx)
    
    def save(self, filepath: str):
        """Save vocabulary to file"""
        import json
        with open(filepath, 'w') as f:
            json.dump({
                'word2idx': self.word2idx,
                'idx2word': {int(k): v for k, v in self.idx2word.items()}
            }, f, indent=2)
        logger.info(f"Saved vocabulary to {filepath}")
    
    def load(self, filepath: str):
        """Load vocabulary from file"""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.word2idx = data['word2idx']
            self.idx2word = {int(k): v for k, v in data['idx2word'].items()}
        logger.info(f"Loaded vocabulary from {filepath}")

