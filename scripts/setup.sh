#!/bin/bash

# Setup script for Audio-to-Sign-Language Converter

echo "Setting up Audio-to-Sign-Language Converter..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    python3 -m venv venv
    source venv/bin/activate
    echo "Virtual environment created and activated"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download NLTK data
echo "Downloading NLTK data..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Create necessary directories
echo "Creating directories..."
mkdir -p data models logs uploads

# Initialize database
echo "Initializing database..."
python3 -c "from ml_pipeline.data_collector import DataCollector; DataCollector()"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: python server.py"
echo "2. Open: http://localhost:5001"
echo ""
echo "For training:"
echo "1. Prepare data: python scripts/prepare_training_data.py"
echo "2. Train model: python scripts/train_translation_model.py"
echo ""

