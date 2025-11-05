"""
ISL Translation Dataset
Custom dataset class for English-ISL translation pairs
"""

import torch
from torch.utils.data import Dataset
import json
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class ISLTranslationDataset(Dataset):
    """Dataset for English-ISL translation pairs"""
    
    def __init__(self, data_path: str, src_vocab, tgt_vocab, max_length: int = 100):
        """
        Initialize dataset
        
        Args:
            data_path: Path to JSON file with translation pairs
            src_vocab: Source vocabulary (English)
            tgt_vocab: Target vocabulary (ISL)
            max_length: Maximum sequence length
        """
        self.src_vocab = src_vocab
        self.tgt_vocab = tgt_vocab
        self.max_length = max_length
        
        # Load data
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        logger.info(f"Loaded {len(self.data)} translation pairs from {data_path}")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get item at index
        
        Returns:
            Tuple of (source_sequence, target_sequence) as tensors
        """
        item = self.data[idx]
        
        # Encode source and target
        src_indices = self.src_vocab.encode(item['english'], max_length=self.max_length)
        tgt_indices = self.tgt_vocab.encode(item['isl'], max_length=self.max_length)
        
        # Convert to tensors
        src_tensor = torch.tensor(src_indices, dtype=torch.long)
        tgt_tensor = torch.tensor(tgt_indices, dtype=torch.long)
        
        return src_tensor, tgt_tensor
    
    @staticmethod
    def create_from_pairs(pairs: List[Tuple[str, str]], output_path: str):
        """
        Create dataset JSON file from translation pairs
        
        Args:
            pairs: List of (english, isl) tuples
            output_path: Path to save JSON file
        """
        data = []
        for eng, isl in pairs:
            data.append({
                'english': eng,
                'isl': isl
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created dataset file with {len(data)} pairs at {output_path}")

