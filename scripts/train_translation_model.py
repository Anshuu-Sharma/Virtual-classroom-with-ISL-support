"""
Main training script for translation model
Can be run locally or on Kaggle
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_pipeline.models.translator import Seq2SeqTranslator
from ml_pipeline.models.translation_trainer import TranslationTrainer
from ml_pipeline.datasets.isl_dataset import ISLTranslationDataset
from ml_pipeline.utils.vocab import Vocabulary
from ml_pipeline.config import ModelConfig
from torch.utils.data import DataLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def prepare_data(config: ModelConfig):
    """Prepare and load vocabularies"""
    # Load training data
    with open(config.TRAIN_DATA_PATH, 'r', encoding='utf-8') as f:
        import json
        train_data = json.load(f)
    
    # Build vocabularies
    src_vocab = Vocabulary()
    tgt_vocab = Vocabulary()
    
    src_texts = [item['english'] for item in train_data]
    tgt_texts = [item['isl'] for item in train_data]
    
    src_vocab.build_vocab(src_texts, min_freq=config.MIN_FREQ)
    tgt_vocab.build_vocab(tgt_texts, min_freq=config.MIN_FREQ)
    
    # Save vocabularies
    src_vocab.save(config.VOCAB_SAVE_PATH.replace('.json', '_src.json'))
    tgt_vocab.save(config.VOCAB_SAVE_PATH.replace('.json', '_tgt.json'))
    
    logger.info(f"Source vocab size: {src_vocab.size()}")
    logger.info(f"Target vocab size: {tgt_vocab.size()}")
    
    return src_vocab, tgt_vocab


def main():
    """Main training function"""
    config = ModelConfig()
    
    # Prepare data
    logger.info("Preparing data...")
    src_vocab, tgt_vocab = prepare_data(config)
    
    # Create datasets
    train_dataset = ISLTranslationDataset(
        config.TRAIN_DATA_PATH, src_vocab, tgt_vocab, config.MAX_LENGTH
    )
    val_dataset = ISLTranslationDataset(
        config.VAL_DATA_PATH, src_vocab, tgt_vocab, config.MAX_LENGTH
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=config.BATCH_SIZE, 
        shuffle=True,
        num_workers=2
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        num_workers=2
    )
    
    # Create model
    logger.info("Creating model...")
    model = Seq2SeqTranslator(
        src_vocab_size=src_vocab.size(),
        tgt_vocab_size=tgt_vocab.size(),
        embed_dim=config.EMBED_DIM,
        hidden_dim=config.HIDDEN_DIM,
        num_layers=config.NUM_LAYERS,
        dropout=config.DROPOUT
    )
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    # Create trainer
    trainer = TranslationTrainer(model, config)
    
    # Train
    trainer.train(train_loader, val_loader)
    
    logger.info("Training completed!")


if __name__ == "__main__":
    main()

