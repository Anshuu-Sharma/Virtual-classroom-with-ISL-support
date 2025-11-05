#!/usr/bin/env python3
"""
Demo script - Test key components without running the full server
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    tests = [
        ("Flask", "flask"),
        ("PyTorch", "torch"),
        ("NLTK", "nltk"),
        ("Whisper Service", "services.asr_service"),
        ("Data Collector", "ml_pipeline.data_collector"),
        ("Translator Model", "ml_pipeline.models.translator"),
    ]
    
    all_ok = True
    for name, module in tests:
        try:
            __import__(module)
            print(f"  [OK] {name}")
        except ImportError as e:
            print(f"  [FAIL] {name}: {e}")
            all_ok = False
    
    return all_ok


def test_whisper():
    """Test Whisper ASR if available"""
    print("\nTesting Whisper ASR...")
    
    try:
        from services.asr_service import get_asr_service
        service = get_asr_service()
        if service:
            print("  [OK] Whisper service initialized")
            return True
        else:
            print("  [SKIP] Whisper not available (optional)")
            return True
    except Exception as e:
        print(f"  [SKIP] Whisper not available: {e}")
        return True


def test_data_collector():
    """Test data collector"""
    print("\nTesting Data Collector...")
    
    try:
        from ml_pipeline.data_collector import DataCollector
        collector = DataCollector()
        print("  [OK] Data collector initialized")
        return True
    except Exception as e:
        print(f"  [FAIL] Data collector: {e}")
        return False


def test_model():
    """Test model creation"""
    print("\nTesting Translation Model...")
    
    try:
        from ml_pipeline.models.translator import Seq2SeqTranslator
        from ml_pipeline.config import ModelConfig
        
        config = ModelConfig()
        model = Seq2SeqTranslator(
            src_vocab_size=1000,
            tgt_vocab_size=1000,
            embed_dim=config.EMBED_DIM,
            hidden_dim=config.HIDDEN_DIM,
            num_layers=config.NUM_LAYERS,
            dropout=config.DROPOUT
        )
        print("  [OK] Model created successfully")
        print(f"      Parameters: {sum(p.numel() for p in model.parameters()):,}")
        return True
    except Exception as e:
        print(f"  [FAIL] Model creation: {e}")
        return False


def test_config():
    """Test configuration"""
    print("\nTesting Configuration...")
    
    try:
        from ml_pipeline.config import ModelConfig
        config = ModelConfig()
        print("  [OK] Configuration loaded")
        print(f"      Batch size: {config.BATCH_SIZE}")
        print(f"      Learning rate: {config.LEARNING_RATE}")
        print(f"      Hidden dim: {config.HIDDEN_DIM}")
        return True
    except Exception as e:
        print(f"  [FAIL] Configuration: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Audio-to-Sign-Language Converter - Component Demo")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Whisper", test_whisper()))
    results.append(("Data Collector", test_data_collector()))
    results.append(("Model", test_model()))
    results.append(("Configuration", test_config()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_ok = True
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
        if not result:
            all_ok = False
    
    if all_ok:
        print("\n[SUCCESS] All components working!")
        print("\nYou can now run the server:")
        print("  python server.py")
        return 0
    else:
        print("\n[WARNING] Some components failed")
        print("Please check the errors above and install missing dependencies")
        return 1


if __name__ == "__main__":
    sys.exit(main())

