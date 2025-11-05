"""
Verify project setup and check all components
"""

import os
import sys
from pathlib import Path


def check_structure():
    """Check project directory structure"""
    print("Checking project structure...")
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    required = [
        "server.py",
        "requirements.txt",
        "services/",
        "ml_pipeline/",
        "data_collection/",
        "evaluation/",
        "scripts/",
        "docs/",
        "kaggle_notebooks/",
        "k8s/"
    ]
    
    all_ok = True
    for item in required:
        path = project_root / item
        if path.exists():
            print(f"  [OK] {item}")
        else:
            print(f"  [MISSING] {item}")
            all_ok = False
    
    return all_ok


def check_key_files():
    """Check key implementation files"""
    print("\nChecking key files...")
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    files = [
        "services/asr_service.py",
        "services/audio_processor.py",
        "ml_pipeline/models/translator.py",
        "ml_pipeline/models/translation_trainer.py",
        "ml_pipeline/data_collector.py",
        "ml_pipeline/preprocessor.py",
        "ml_pipeline/evaluator.py",
        "Dockerfile",
        "docker-compose.yml",
        "kaggle_notebooks/train_translation_model.ipynb"
    ]
    
    all_ok = True
    for file in files:
        path = project_root / file
        if path.exists():
            print(f"  [OK] {file}")
        else:
            print(f"  [MISSING] {file}")
            all_ok = False
    
    return all_ok


def main():
    """Run verification"""
    print("=" * 60)
    print("Project Setup Verification")
    print("=" * 60)
    
    structure_ok = check_structure()
    files_ok = check_key_files()
    
    print("\n" + "=" * 60)
    if structure_ok and files_ok:
        print("[SUCCESS] All components verified!")
        print("\nProject is ready to use.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Test installation: python scripts/test_installation.py")
        print("  3. Run server: python server.py")
        return 0
    else:
        print("[WARNING] Some components missing.")
        print("Please check the files listed above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

