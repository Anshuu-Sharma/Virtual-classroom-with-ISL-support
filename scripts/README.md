# Scripts Directory

Utility scripts for the Audio-to-Sign-Language Converter project.

## Quick Start Scripts

### Windows
- **`run.bat`** - Quick start script (runs the server)
- **`setup.bat`** - Setup script (installs dependencies)

### Cross-Platform
- **`quick_start.py`** - Interactive setup and run script
- **`demo.py`** - Test components without running full server

## Training Scripts

- **`train_translation_model.py`** - Train the translation model locally
- **`prepare_training_data.py`** - Prepare training data from SiGML files
- **`evaluate_models.py`** - Evaluate model performance

## Deployment Scripts

- **`deploy.sh`** - Deploy to Kubernetes (Linux/Mac)
- **`setup.sh`** - Setup script (Linux/Mac)

## Utility Scripts

- **`test_installation.py`** - Test if installation is complete
- **`verify_setup.py`** - Verify project structure
- **`setup_kaggle.py`** - Prepare files for Kaggle
- **`create_kaggle_dataset.py`** - Create Kaggle dataset
- **`upload_to_kaggle.py`** - Upload to Kaggle
- **`download_from_kaggle.py`** - Download from Kaggle

## Usage Examples

### Windows

```batch
REM Setup
setup.bat

REM Run server
run.bat
```

### Cross-Platform

```bash
# Quick start (interactive)
python scripts/quick_start.py

# Test components
python scripts/demo.py

# Verify setup
python scripts/verify_setup.py

# Test installation
python scripts/test_installation.py
```

## Script Details

### quick_start.py
Interactive script that:
1. Checks Python version
2. Checks/installs dependencies
3. Verifies setup
4. Optionally runs the server

### demo.py
Non-interactive test script that:
1. Tests all imports
2. Tests Whisper ASR
3. Tests data collector
4. Tests model creation
5. Tests configuration

### verify_setup.py
Checks project structure and key files are present.

### test_installation.py
Comprehensive test of:
- All dependencies
- Project structure
- Key components

