"""
Test installation and verify all components are working
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    errors = []
    
    # Test basic Python packages
    try:
        import flask
        print("  ✅ Flask")
    except ImportError as e:
        errors.append(f"Flask: {e}")
        print("  ❌ Flask")
    
    try:
        import torch
        print(f"  ✅ PyTorch (version: {torch.__version__})")
        if torch.cuda.is_available():
            print(f"     GPU available: {torch.cuda.get_device_name(0)}")
        else:
            print("     GPU not available (using CPU)")
    except ImportError as e:
        errors.append(f"PyTorch: {e}")
        print("  ❌ PyTorch")
    
    try:
        import whisper
        print("  ✅ Whisper")
    except ImportError as e:
        errors.append(f"Whisper: {e}")
        print("  ❌ Whisper (optional - install with: pip install openai-whisper)")
    
    try:
        import nltk
        print("  ✅ NLTK")
    except ImportError as e:
        errors.append(f"NLTK: {e}")
        print("  ❌ NLTK")
    
    # Test project modules
    try:
        from services.asr_service import ASRService
        print("  ✅ ASR Service")
    except ImportError as e:
        errors.append(f"ASR Service: {e}")
        print("  ❌ ASR Service")
    
    try:
        from ml_pipeline.models.translator import Seq2SeqTranslator
        print("  ✅ Translation Model")
    except ImportError as e:
        errors.append(f"Translation Model: {e}")
        print("  ❌ Translation Model")
    
    try:
        from ml_pipeline.data_collector import DataCollector
        print("  ✅ Data Collector")
    except ImportError as e:
        errors.append(f"Data Collector: {e}")
        print("  ❌ Data Collector")
    
    try:
        from ml_pipeline.evaluator import ModelEvaluator
        print("  ✅ Model Evaluator")
    except ImportError as e:
        errors.append(f"Model Evaluator: {e}")
        print("  ❌ Model Evaluator")
    
    return errors


def test_directories():
    """Test required directories exist"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "services",
        "ml_pipeline",
        "ml_pipeline/models",
        "ml_pipeline/datasets",
        "ml_pipeline/utils",
        "data_collection",
        "evaluation",
        "scripts",
        "kaggle_notebooks",
        "docs"
    ]
    
    missing = []
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}/")
        else:
            missing.append(dir_path)
            print(f"  ❌ {dir_path}/ (missing)")
    
    return missing


def test_files():
    """Test critical files exist"""
    print("\nTesting critical files...")
    
    required_files = [
        "server.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "services/asr_service.py",
        "ml_pipeline/models/translator.py",
        "ml_pipeline/config.py"
    ]
    
    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            missing.append(file_path)
            print(f"  ❌ {file_path} (missing)")
    
    return missing


def main():
    """Run all tests"""
    print("=" * 60)
    print("Audio-to-Sign-Language Converter - Installation Test")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    sys.path.insert(0, str(project_dir))
    
    # Run tests
    import_errors = test_imports()
    missing_dirs = test_directories()
    missing_files = test_files()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if not import_errors and not missing_dirs and not missing_files:
        print("✅ All tests passed! Installation is complete.")
        print("\nNext steps:")
        print("  1. Run: python server.py")
        print("  2. Open: http://localhost:5001")
        return 0
    else:
        print("⚠️  Some issues found:")
        if import_errors:
            print(f"\n  Import errors: {len(import_errors)}")
            for error in import_errors:
                print(f"    - {error}")
        if missing_dirs:
            print(f"\n  Missing directories: {len(missing_dirs)}")
            for dir_path in missing_dirs:
                print(f"    - {dir_path}/")
        if missing_files:
            print(f"\n  Missing files: {len(missing_files)}")
            for file_path in missing_files:
                print(f"    - {file_path}")
        
        print("\nTo fix:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Check file structure")
        return 1


if __name__ == "__main__":
    sys.exit(main())

