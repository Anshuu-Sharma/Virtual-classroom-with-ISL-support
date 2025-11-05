"""
Evaluate ASR and Translation models
"""

import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_pipeline.evaluator import ModelEvaluator
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_asr_model(test_file: str):
    """Evaluate ASR model"""
    evaluator = ModelEvaluator()
    
    # Load test data
    with open(test_file, 'r') as f:
        test_data = json.load(f)
    
    references = [item['reference'] for item in test_data]
    hypotheses = [item['hypothesis'] for item in test_data]
    
    # Evaluate
    metrics = evaluator.evaluate_asr(references, hypotheses)
    
    logger.info("ASR Evaluation Results:")
    logger.info(f"  WER: {metrics['wer']:.4f} ± {metrics['wer_std']:.4f}")
    logger.info(f"  Accuracy: {metrics['accuracy']:.4f} ± {metrics['accuracy_std']:.4f}")
    
    return metrics


def evaluate_translation_model(test_file: str):
    """Evaluate translation model"""
    evaluator = ModelEvaluator()
    
    # Load test data
    with open(test_file, 'r') as f:
        test_data = json.load(f)
    
    references = [[item['reference']] for item in test_data]  # List of lists
    hypotheses = [item['hypothesis'] for item in test_data]
    
    # Evaluate
    metrics = evaluator.evaluate_translation(references, hypotheses)
    
    logger.info("Translation Evaluation Results:")
    logger.info(f"  BLEU: {metrics['bleu']:.4f} ± {metrics['bleu_std']:.4f}")
    logger.info(f"  ROUGE-L: {metrics['rouge_l']:.4f} ± {metrics['rouge_l_std']:.4f}")
    
    return metrics


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate models')
    parser.add_argument('--asr', type=str, help='ASR test file path')
    parser.add_argument('--translation', type=str, help='Translation test file path')
    
    args = parser.parse_args()
    
    if args.asr:
        evaluate_asr_model(args.asr)
    
    if args.translation:
        evaluate_translation_model(args.translation)

