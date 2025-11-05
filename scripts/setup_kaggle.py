"""
Setup script for Kaggle - prepares everything needed for Kaggle training
"""

import os
import shutil
import json
from pathlib import Path


def setup_kaggle_environment():
    """Prepare Kaggle environment with all necessary files"""
    
    print("🚀 Setting up Kaggle environment...")
    
    # Create kaggle_working directory
    kaggle_dir = Path("kaggle_working")
    kaggle_dir.mkdir(exist_ok=True)
    
    # Copy ml_pipeline directory
    if Path("ml_pipeline").exists():
        print("📦 Copying ml_pipeline/...")
        if (kaggle_dir / "ml_pipeline").exists():
            shutil.rmtree(kaggle_dir / "ml_pipeline")
        shutil.copytree("ml_pipeline", kaggle_dir / "ml_pipeline")
        print("  ✅ ml_pipeline/ copied")
    else:
        print("  ⚠️  ml_pipeline/ not found")
    
    # Copy scripts
    scripts_dir = kaggle_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    scripts_to_copy = [
        "scripts/train_translation_model.py",
        "scripts/prepare_training_data.py"
    ]
    
    for script in scripts_to_copy:
        if Path(script).exists():
            shutil.copy(script, scripts_dir)
            print(f"  ✅ {script} copied")
    
    # Copy notebooks
    notebooks_dir = kaggle_dir / "notebooks"
    notebooks_dir.mkdir(exist_ok=True)
    
    notebooks_to_copy = [
        "kaggle_notebooks/train_translation_model.ipynb",
        "kaggle_notebooks/dataset_analysis.ipynb"
    ]
    
    for notebook in notebooks_to_copy:
        if Path(notebook).exists():
            shutil.copy(notebook, notebooks_dir)
            print(f"  ✅ {notebook} copied")
    
    # Create instructions file
    instructions = """
# Kaggle Upload Instructions

## Files to Upload

### 1. Dataset (to Kaggle Datasets)
- Upload from: kaggle_datasets/isl-translation-dataset/
- Files: train_pairs.json, val_pairs.json

### 2. Code (to Kaggle Notebook)
- Upload ml_pipeline/ directory to /kaggle/working/
- Or copy contents from kaggle_working/ml_pipeline/

### 3. Notebook
- Use: notebooks/train_translation_model.ipynb
- Or copy contents to new Kaggle notebook

## Steps

1. Create Kaggle dataset:
   - Go to https://www.kaggle.com/datasets
   - Upload train_pairs.json and val_pairs.json
   - Note the dataset name

2. Create Kaggle notebook:
   - Go to https://www.kaggle.com/code
   - Create new notebook
   - Enable GPU (T4 x2)

3. Add dataset to notebook:
   - Click "Add Data"
   - Search for your dataset
   - Add it

4. Upload code:
   - Upload ml_pipeline/ folder
   - Extract to /kaggle/working/

5. Run training:
   - Copy notebook contents
   - Update dataset path if needed
   - Run all cells

## Download Results

After training, download:
- models/lstm_translator.pth
- vocab_src.json
- vocab_tgt.json

Place in your local models/ directory.
"""
    
    with open(kaggle_dir / "KAGGLE_INSTRUCTIONS.txt", 'w') as f:
        f.write(instructions)
    
    print(f"\n✅ Kaggle environment setup complete!")
    print(f"📁 Files prepared in: {kaggle_dir}/")
    print(f"\n📖 Next steps:")
    print(f"  1. Review {kaggle_dir}/KAGGLE_INSTRUCTIONS.txt")
    print(f"  2. Upload dataset to Kaggle")
    print(f"  3. Upload ml_pipeline/ to Kaggle notebook")
    print(f"  4. Run training notebook")


if __name__ == "__main__":
    setup_kaggle_environment()

