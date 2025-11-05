"""
Upload dataset to Kaggle
Requires kaggle API token
"""

import os
import json
import zipfile
from pathlib import Path
import subprocess


def create_kaggle_dataset(dataset_name: str, data_dir: str = "data"):
    """Create Kaggle dataset from local data"""
    
    # Create dataset directory
    dataset_dir = Path(f"kaggle_datasets/{dataset_name}")
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy data files
    data_path = Path(data_dir)
    if data_path.exists():
        # Copy training files
        train_file = data_path / "train_pairs.json"
        val_file = data_path / "val_pairs.json"
        
        if train_file.exists():
            import shutil
            shutil.copy(train_file, dataset_dir / "train_pairs.json")
        if val_file.exists():
            import shutil
            shutil.copy(val_file, dataset_dir / "val_pairs.json")
    
    # Create dataset-metadata.json
    metadata = {
        "title": dataset_name,
        "id": f"your-username/{dataset_name}",
        "licenses": [{"name": "CC0-1.0"}]
    }
    
    with open(dataset_dir / "dataset-metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Dataset created in {dataset_dir}")
    print(f"\nTo upload to Kaggle:")
    print(f"1. Install kaggle: pip install kaggle")
    print(f"2. Set up API token: ~/.kaggle/kaggle.json")
    print(f"3. Run: cd {dataset_dir} && kaggle datasets create")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create Kaggle dataset')
    parser.add_argument('--name', type=str, default='isl-translation-dataset',
                       help='Dataset name')
    parser.add_argument('--data-dir', type=str, default='data',
                       help='Data directory')
    
    args = parser.parse_args()
    create_kaggle_dataset(args.name, args.data_dir)

