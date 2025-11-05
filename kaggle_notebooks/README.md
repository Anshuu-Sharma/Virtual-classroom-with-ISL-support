# Kaggle Notebooks

This directory contains Jupyter notebooks for training and analyzing the translation model on Kaggle.

## Notebooks

### 1. `train_translation_model.ipynb`
Complete training notebook for the LSTM Seq2Seq translation model.

**Features:**
- GPU support (free T4 x2)
- Complete training pipeline
- Model checkpointing
- Vocabulary building
- Model evaluation

**Usage:**
1. Upload this notebook to Kaggle
2. Add your dataset (train_pairs.json, val_pairs.json)
3. Upload ml_pipeline/ directory to /kaggle/working/
4. Enable GPU accelerator
5. Run all cells

### 2. `dataset_analysis.ipynb`
Dataset analysis and exploration notebook.

**Features:**
- Dataset statistics
- Length distribution analysis
- Vocabulary analysis
- Quality checks
- Visualizations

**Usage:**
1. Upload this notebook to Kaggle
2. Add your dataset
3. Run all cells to analyze

## Quick Start

### Step 1: Prepare Dataset

```bash
# On your local machine
python scripts/prepare_training_data.py
python scripts/create_kaggle_dataset.py
```

### Step 2: Upload to Kaggle

1. Go to https://www.kaggle.com/datasets
2. Click "New Dataset"
3. Upload files from `kaggle_datasets/isl-translation-dataset/`
4. Make dataset public or private

### Step 3: Create Notebook

1. Go to https://www.kaggle.com/code
2. Click "New Notebook"
3. Copy contents from `train_translation_model.ipynb`
4. Add your dataset
5. Enable GPU (T4 x2)

### Step 4: Upload Code

Upload the `ml_pipeline/` directory:
1. Click "Add Data" → "Upload"
2. Upload `ml_pipeline/` folder
3. Extract to `/kaggle/working/`

### Step 5: Train

1. Run all cells
2. Monitor training progress
3. Download trained model from "Output" tab

## Files to Download After Training

- `models/lstm_translator.pth` - Model weights
- `vocab_src.json` - Source vocabulary (English)
- `vocab_tgt.json` - Target vocabulary (ISL)

## Tips

- **GPU Time**: 30 hours/week free
- **Save Checkpoints**: Save model every few epochs
- **Monitor Progress**: Watch loss values
- **Early Stopping**: Model will stop if validation loss doesn't improve
- **Download Regularly**: Download intermediate checkpoints

## Troubleshooting

### Dataset Not Found
- Verify dataset is added to notebook
- Check dataset path matches your dataset name
- Ensure files are named correctly

### Import Errors
- Make sure ml_pipeline/ is uploaded
- Check file paths in notebook
- Verify all dependencies are installed

### GPU Not Available
- Check accelerator is set to GPU
- Verify notebook is running (not saved)
- Wait if quota exceeded

