"""
Prepare training data from existing SiGML files and rule-based translations
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_pipeline.data_collector import DataCollector
from ml_pipeline.preprocessor import DataPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_sigml_files(base_dir: str = "SignFiles") -> list:
    """Load existing SiGML files and extract English-ISL pairs"""
    sigml_dir = Path(base_dir)
    pairs = []
    
    # Load words.txt for eligible words
    words_file = Path("words.txt")
    eligible_words = set()
    if words_file.exists():
        with open(words_file, 'r') as f:
            content = f.read()
            # Parse the words from the file
            import re
            words = re.findall(r"'([^']+)'", content)
            eligible_words = set(words)
    
    # Load sigmlFiles.json for mappings
    sigml_json = Path("js/sigmlFiles.json")
    sigml_mappings = {}
    if sigml_json.exists():
        with open(sigml_json, 'r') as f:
            # Skip first line (var sigmlList =)
            content = f.read()
            # Extract JSON array
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                sigml_list = json.loads(json_str)
                for item in sigml_list:
                    sigml_mappings[item['name']] = item['fileName']
    
    # Create pairs from mappings
    for word, sigml_file in sigml_mappings.items():
        if word and word not in ['EOL', '']:
            # English word -> ISL gloss (word itself for now)
            pairs.append((word.lower(), word.lower()))
    
    logger.info(f"Loaded {len(pairs)} pairs from SiGML files")
    return pairs


def create_training_data():
    """Create training data from various sources"""
    preprocessor = DataPreprocessor()
    collector = DataCollector()
    
    # Load existing SiGML pairs
    logger.info("Loading SiGML files...")
    sigml_pairs = load_sigml_files()
    
    # Add to database and create training files
    training_pairs = []
    for eng, isl in sigml_pairs:
        pair_id = collector.add_translation_pair(
            english_text=eng,
            isl_text=isl,
            source="sigml_files",
            verified=True
        )
        training_pairs.append((eng, isl))
    
    # Preprocess pairs
    preprocessed_pairs = []
    for eng, isl in training_pairs:
        preprocessed_eng, preprocessed_isl = preprocessor.preprocess_pair(eng, isl)
        preprocessed_pairs.append((preprocessed_eng, preprocessed_isl))
    
    # Split into train/val (80/20)
    split_idx = int(len(preprocessed_pairs) * 0.8)
    train_pairs = preprocessed_pairs[:split_idx]
    val_pairs = preprocessed_pairs[split_idx:]
    
    # Save to JSON files
    train_data = [{'english': eng, 'isl': isl} for eng, isl in train_pairs]
    val_data = [{'english': eng, 'isl': isl} for eng, isl in val_pairs]
    
    os.makedirs("data", exist_ok=True)
    with open("data/train_pairs.json", 'w', encoding='utf-8') as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)
    with open("data/val_pairs.json", 'w', encoding='utf-8') as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created training data: {len(train_pairs)} train, {len(val_pairs)} val")
    
    # Export from database
    collector.export_to_json("data/all_pairs.json", verified_only=True)


if __name__ == "__main__":
    create_training_data()

