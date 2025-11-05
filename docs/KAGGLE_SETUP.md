# Kaggle Setup Guide

## Overview

This guide explains how to use Kaggle for training your translation model with free GPU resources.

## Prerequisites

1. Kaggle account (free): https://www.kaggle.com/account/register
2. Kaggle API token

## Setup Kaggle API

### 1. Get API Token

1. Go to https://www.kaggle.com/account
2. Scroll to "API" section
3. Click "Create New Token"
4. Download `kaggle.json` file

### 2. Install Kaggle CLI

```bash
pip install kaggle
```

### 3. Setup Token

**Windows:**
```bash
mkdir %USERPROFILE%\.kaggle
copy kaggle.json %USERPROFILE%\.kaggle\
```

**Linux/Mac:**
```bash
mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

## Prepare Dataset for Kaggle

### Step 1: Prepare Training Data

```bash
python scripts/prepare_training_data.py
```

This creates:
- `data/train_pairs.json`
- `data/val_pairs.json`

### Step 2: Create Kaggle Dataset

```bash
python scripts/create_kaggle_dataset.py
```

This creates a folder ready for Kaggle upload.

### Step 3: Upload Dataset

```bash
cd kaggle_datasets/isl-translation-dataset
kaggle datasets create -r zip
```

Or upload manually:
1. Go to https://www.kaggle.com/datasets
2. Click "New Dataset"
3. Upload files
4. Set visibility (Public/Private)

## Using Kaggle Notebooks

### Step 1: Create New Notebook

1. Go to https://www.kaggle.com/code
2. Click "New Notebook"
3. Select GPU accelerator (T4 x2 - free)

### Step 2: Add Dataset

1. Click "Add Data"
2. Search for your dataset
3. Add it to the notebook

### Step 3: Upload Code

Option A: Upload project files
- Upload `ml_pipeline/` directory
- Upload `scripts/` directory

Option B: Use provided notebook
- Copy contents from `kaggle_notebooks/train_translation_model.ipynb`
- Or upload the notebook file directly

### Step 4: Run Training

1. Update dataset path in notebook
2. Run all cells
3. Training will use GPU automatically

### Step 5: Download Model

After training completes:
1. Go to "Output" tab
2. Download:
   - `models/lstm_translator.pth`
   - `vocab_src.json`
   - `vocab_tgt.json`

## Kaggle Resources

### Free GPU Limits
- **30 hours/week** of GPU time
- **T4 x2** (2x T4 GPUs) available
- Resets weekly

### Tips for Efficient Training

1. **Use GPU efficiently:**
   - Batch size: 32-64
   - Use mixed precision training

2. **Save checkpoints:**
   - Save model every few epochs
   - Download intermediate checkpoints

3. **Monitor progress:**
   - Use tqdm for progress bars
   - Log metrics to output

4. **Time management:**
   - Plan training within 9-hour sessions
   - Use early stopping

## Troubleshooting

### GPU Not Available
- Check accelerator is set to GPU
- Verify notebook is running (not saved)
- Wait if GPU quota exceeded

### Out of Memory
- Reduce batch size
- Reduce model size
- Use gradient checkpointing

### Dataset Not Found
- Verify dataset is added to notebook
- Check dataset path in code
- Ensure dataset is public or you have access

## Example Usage

### Quick Start

```python
# In Kaggle Notebook
!pip install torch torchvision torchaudio

# Add your dataset
# Path: /kaggle/input/isl-translation-dataset/

# Upload your code
# Copy ml_pipeline/ directory to /kaggle/working/

# Run training
!python scripts/train_translation_model.py
```

### Download Trained Model

```python
# In Kaggle Notebook Output
import shutil

# Model files are in /kaggle/working/
# Download via Kaggle UI or:
shutil.copy('/kaggle/working/models/lstm_translator.pth', '/kaggle/working/')
```

## Alternative: Use Kaggle Notebook Template

1. Upload `kaggle_notebooks/train_translation_model.ipynb` to Kaggle
2. Add your dataset
3. Run all cells
4. Download results

This is the easiest way to get started!

