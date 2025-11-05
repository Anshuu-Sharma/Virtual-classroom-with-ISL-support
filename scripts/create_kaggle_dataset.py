"""
Create and prepare dataset for Kaggle upload
"""

import json
import os
from pathlib import Path
import shutil


def create_kaggle_dataset(dataset_name: str = "isl-translation-dataset", 
                         source_dir: str = "data",
                         output_dir: str = "kaggle_datasets"):
    """
    Create Kaggle dataset from local data files
    
    Args:
        dataset_name: Name for the Kaggle dataset
        source_dir: Source directory with data files
        output_dir: Output directory for Kaggle dataset
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir) / dataset_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Copy data files
    files_to_copy = ['train_pairs.json', 'val_pairs.json', 'test_pairs.json']
    copied_files = []
    
    for filename in files_to_copy:
        src_file = source_path / filename
        if src_file.exists():
            dst_file = output_path / filename
            shutil.copy(src_file, dst_file)
            copied_files.append(filename)
            print(f"Copied {filename}")
    
    # Create dataset-metadata.json
    metadata = {
        "title": dataset_name.replace('-', ' ').title(),
        "id": f"your-username/{dataset_name}",
        "licenses": [
            {
                "name": "CC0-1.0"
            }
        ]
    }
    
    metadata_file = output_path / "dataset-metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Dataset created in: {output_path}")
    print(f"\n📁 Files included: {', '.join(copied_files)}")
    print(f"\n📝 Next steps:")
    print(f"1. Review dataset-metadata.json and update 'id' with your Kaggle username")
    print(f"2. Install Kaggle CLI: pip install kaggle")
    print(f"3. Set up API token: ~/.kaggle/kaggle.json")
    print(f"4. Navigate to dataset directory: cd {output_path}")
    print(f"5. Create dataset: kaggle datasets create -r zip")
    print(f"\nOr upload manually at: https://www.kaggle.com/datasets")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create Kaggle dataset')
    parser.add_argument('--name', type=str, default='isl-translation-dataset',
                       help='Dataset name')
    parser.add_argument('--source', type=str, default='data',
                       help='Source data directory')
    parser.add_argument('--output', type=str, default='kaggle_datasets',
                       help='Output directory')
    
    args = parser.parse_args()
    create_kaggle_dataset(args.name, args.source, args.output)

