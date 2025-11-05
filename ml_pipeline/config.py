"""
Configuration for ML Pipeline
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Model configuration
class ModelConfig:
    """LSTM Seq2Seq model configuration"""
    
    # Architecture
    EMBED_DIM = 256
    HIDDEN_DIM = 512
    NUM_LAYERS = 2
    DROPOUT = 0.3
    
    # Training
    BATCH_SIZE = 32
    LEARNING_RATE = 0.001
    NUM_EPOCHS = 50
    GRAD_CLIP = 5.0
    
    # Data
    MAX_LENGTH = 100
    MIN_FREQ = 2
    
    # Paths
    MODEL_SAVE_PATH = str(MODELS_DIR / "lstm_translator.pth")
    VOCAB_SAVE_PATH = str(MODELS_DIR / "vocab.json")
    TRAIN_DATA_PATH = str(DATA_DIR / "train_pairs.json")
    VAL_DATA_PATH = str(DATA_DIR / "val_pairs.json")
    
    # Kaggle paths (if running on Kaggle)
    KAGGLE_DATA_PATH = "/kaggle/input/isl-translation-dataset"
    KAGGLE_WORKING_PATH = "/kaggle/working"
    
    # Device
    DEVICE = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu"

# Training configuration
TRAINING_CONFIG = {
    "early_stopping_patience": 5,
    "save_best_model": True,
    "log_interval": 100,
    "eval_interval": 1,
    "checkpoint_interval": 5
}

