"""
Download trained models from Kaggle
"""

import os
import subprocess
from pathlib import Path


def download_model_from_kaggle(dataset_name: str, output_dir: str = "models"):
    """
    Download trained model from Kaggle dataset
    
    Args:
        dataset_name: Kaggle dataset name (username/dataset-name)
        output_dir: Output directory for models
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"Downloading model from Kaggle dataset: {dataset_name}")
    
    # Use Kaggle API to download
    cmd = [
        "kaggle", "datasets", "download", 
        "-d", dataset_name,
        "-p", str(output_path),
        "--unzip"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Model downloaded to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading: {e}")
        print("\nMake sure you have:")
        print("1. Installed kaggle: pip install kaggle")
        print("2. Set up API token: ~/.kaggle/kaggle.json")
        print("3. Accepted dataset terms on Kaggle website")
    except FileNotFoundError:
        print("Kaggle CLI not found. Install with: pip install kaggle")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download model from Kaggle')
    parser.add_argument('--dataset', type=str, required=True,
                       help='Kaggle dataset name (username/dataset-name)')
    parser.add_argument('--output', type=str, default='models',
                       help='Output directory')
    
    args = parser.parse_args()
    download_model_from_kaggle(args.dataset, args.output)

