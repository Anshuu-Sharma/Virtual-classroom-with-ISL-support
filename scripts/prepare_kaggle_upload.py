"""
Prepare Kaggle Dataset Upload Package
Creates a properly formatted dataset folder with metadata for Kaggle upload
"""

import json
import shutil
import zipfile
from pathlib import Path
import sys

def create_kaggle_dataset():
    """Create Kaggle dataset upload package"""
    
    print("="*60)
    print("Preparing Kaggle Dataset Upload Package")
    print("="*60)
    
    # Paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    models_dir = base_dir / "models"
    kaggle_datasets_dir = base_dir / "kaggle_datasets"
    dataset_dir = kaggle_datasets_dir / "isl-translation-dataset"
    
    # Create directories
    kaggle_datasets_dir.mkdir(exist_ok=True)
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
    dataset_dir.mkdir(exist_ok=True)
    
    print("\n1. Copying data files...")
    
    # Copy training data files
    files_to_copy = [
        (data_dir / "train_pairs_enhanced.json", "train_pairs_enhanced.json"),
        (data_dir / "val_pairs_enhanced.json", "val_pairs_enhanced.json"),
        (models_dir / "vocab_src.json", "vocab_src.json"),
        (models_dir / "vocab_tgt.json", "vocab_tgt.json"),
    ]
    
    for src, dest_name in files_to_copy:
        if src.exists():
            dest = dataset_dir / dest_name
            shutil.copy2(src, dest)
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"   ✅ Copied {dest_name} ({size_mb:.2f} MB)")
        else:
            print(f"   ⚠️  Warning: {src} not found, skipping")
    
    print("\n2. Creating dataset metadata...")
    
    # Create dataset-metadata.json
    metadata = {
        "title": "ISL Translation Training Data",
        "id": "your-username/isl-translation-dataset",
        "licenses": [{"name": "CC0-1.0"}],
        "keywords": ["sign-language", "indian-sign-language", "translation", "nlp", "lstm"],
        "collaborators": [],
        "data": []
    }
    
    metadata_path = dataset_dir / "dataset-metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✅ Created dataset-metadata.json")
    
    print("\n3. Creating README.md...")
    
    # Create README
    readme_content = """# ISL Translation Training Data

## Description

This dataset contains training and validation pairs for English-to-Indian Sign Language (ISL) translation.

## Contents

- `train_pairs_enhanced.json` - Training pairs with ISL grammar (735 pairs)
- `val_pairs_enhanced.json` - Validation pairs (184 pairs)
- `vocab_src.json` - Source vocabulary (English)
- `vocab_tgt.json` - Target vocabulary (ISL)

## Data Format

Each JSON file contains an array of translation pairs:

```json
{
  "english": "<sos> hello how are you <eos>",
  "isl": "<sos> hello you fine how <eos>"
}
```

## ISL Grammar Rules Applied

- SOV (Subject-Object-Verb) word order
- Removal of articles (a, an, the)
- Removal of auxiliary verbs (am, is, are, was, were, etc.)
- WH-questions placed at end of sentence
- Topic-comment structure

## Usage

This dataset is designed for training LSTM Seq2Seq models for English-to-ISL translation.

## Model Architecture

- Encoder: Bidirectional LSTM
- Decoder: LSTM with attention
- Embedding dimension: 256
- Hidden dimension: 512
- Number of layers: 2

## Citation

If you use this dataset, please cite:
```
Virtual Classroom with ISL Support
Indian Sign Language Translation Dataset
```

## License

CC0-1.0 (Public Domain)
"""
    
    readme_path = dataset_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    print(f"   ✅ Created README.md")
    
    print("\n4. Creating ZIP file...")
    
    # Create ZIP file
    zip_path = kaggle_datasets_dir / "isl-translation-dataset.zip"
    if zip_path.exists():
        zip_path.unlink()
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in dataset_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(dataset_dir)
                zipf.write(file_path, arcname)
                print(f"   ✅ Added {arcname} to ZIP")
    
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Created ZIP file: {zip_path}")
    print(f"   Size: {zip_size_mb:.2f} MB")
    
    print("\n" + "="*60)
    print("✅ Kaggle dataset package ready!")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Go to: https://www.kaggle.com/datasets")
    print("2. Click: 'New Dataset'")
    print("3. Upload: " + str(zip_path))
    print("4. Title: 'ISL Translation Training Data'")
    print("5. Make it: Private (for now)")
    print("6. Click: 'Create'")
    print("\nThen copy your dataset URL (format: username/isl-translation-dataset)")
    print("="*60)
    
    return zip_path

if __name__ == "__main__":
    create_kaggle_dataset()

