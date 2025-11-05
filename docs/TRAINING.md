# Model Training Guide

## Overview

This guide explains how to train the LSTM Seq2Seq translation model for English-to-ISL translation.

## Prerequisites

- Python 3.9+
- PyTorch 1.12+
- CUDA (optional, for GPU training)
- Kaggle account (for free GPU training)

## Data Preparation

### Step 1: Prepare Training Data

```bash
python scripts/prepare_training_data.py
```

This script:
- Loads existing SiGML files
- Creates English-ISL pairs
- Splits into train/validation sets
- Saves to `data/train_pairs.json` and `data/val_pairs.json`

### Step 2: Verify Data

Check the generated files:
```bash
cat data/train_pairs.json
```

## Training on Local Machine

### Basic Training

```bash
python scripts/train_translation_model.py
```

### Configuration

Edit `ml_pipeline/config.py` to adjust:
- Model architecture (embed_dim, hidden_dim, num_layers)
- Training hyperparameters (batch_size, learning_rate, epochs)
- Data paths

## Training on Kaggle (Recommended)

### Step 1: Create Kaggle Notebook

1. Go to [Kaggle Notebooks](https://www.kaggle.com/code)
2. Create new notebook
3. Upload training data as dataset

### Step 2: Setup Notebook

```python
# Install dependencies
!pip install torch torchvision torchaudio

# Upload your code
# - ml_pipeline/
# - scripts/train_translation_model.py
# - data/train_pairs.json
# - data/val_pairs.json
```

### Step 3: Enable GPU

In Kaggle notebook settings:
- Accelerator: GPU T4 x2 (free tier)

### Step 4: Run Training

```python
# In notebook
!python scripts/train_translation_model.py
```

### Step 5: Download Model

After training, download:
- `models/lstm_translator.pth` (model weights)
- `models/vocab_src.json` (source vocabulary)
- `models/vocab_tgt.json` (target vocabulary)

## Training Parameters

### Model Configuration
- **Embedding Dimension**: 256
- **Hidden Dimension**: 512
- **Number of Layers**: 2
- **Dropout**: 0.3

### Training Configuration
- **Batch Size**: 32
- **Learning Rate**: 0.001
- **Epochs**: 50
- **Gradient Clipping**: 5.0
- **Early Stopping Patience**: 5

## Monitoring Training

Training progress includes:
- Train loss per epoch
- Validation loss per epoch
- Learning rate adjustments
- Model checkpoints

## Model Evaluation

After training, evaluate the model:

```bash
python scripts/evaluate_models.py --translation data/test_pairs.json
```

Metrics:
- BLEU score
- ROUGE-L score
- Word Error Rate (WER)

## Troubleshooting

### Out of Memory
- Reduce batch size
- Reduce model size (hidden_dim)
- Use gradient accumulation

### Slow Training
- Enable GPU
- Use Kaggle GPU (free 30 hrs/week)
- Reduce data size for testing

### Poor Accuracy
- Increase training data
- Adjust learning rate
- Increase model capacity
- Train for more epochs

