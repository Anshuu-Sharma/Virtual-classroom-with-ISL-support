"""
Model Evaluation Module
Contains metrics for ASR and translation evaluation
"""

import logging
from typing import List, Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ASREvaluator:
    """Evaluate Automatic Speech Recognition models"""
    
    @staticmethod
    def calculate_wer(reference: str, hypothesis: str) -> float:
        """
        Calculate Word Error Rate (WER)
        
        WER = (S + D + I) / N
        where:
        S = substitutions
        D = deletions
        I = insertions
        N = number of words in reference
        
        Args:
            reference: Ground truth text
            hypothesis: Predicted text
            
        Returns:
            WER score (lower is better, 0.0 = perfect)
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        # Create distance matrix using dynamic programming
        n = len(ref_words)
        m = len(hyp_words)
        
        # Initialize DP table
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        
        # Base cases
        for i in range(n + 1):
            dp[i][0] = i  # Deletions
        for j in range(m + 1):
            dp[0][j] = j  # Insertions
        
        # Fill DP table
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    dp[i][j] = dp[i-1][j-1]  # Match
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,      # Deletion
                        dp[i][j-1] + 1,      # Insertion
                        dp[i-1][j-1] + 1     # Substitution
                    )
        
        # Calculate WER
        if n == 0:
            return 1.0 if m > 0 else 0.0
        
        wer = dp[n][m] / n
        return wer
    
    @staticmethod
    def calculate_accuracy(reference: str, hypothesis: str) -> float:
        """
        Calculate word-level accuracy
        
        Returns:
            Accuracy score (0.0 to 1.0, higher is better)
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if len(ref_words) == 0:
            return 1.0 if len(hyp_words) == 0 else 0.0
        
        matches = sum(1 for r, h in zip(ref_words, hyp_words) if r == h)
        accuracy = matches / len(ref_words)
        
        return accuracy


class TranslationEvaluator:
    """Evaluate translation models"""
    
    @staticmethod
    def calculate_bleu(reference: List[str], hypothesis: str, n: int = 4) -> float:
        """
        Calculate BLEU score (simplified version)
        
        Args:
            reference: List of reference translations
            hypothesis: Predicted translation
            n: Maximum n-gram order
            
        Returns:
            BLEU score (0.0 to 1.0, higher is better)
        """
        if not reference or not hypothesis:
            return 0.0
        
        # Use first reference if multiple
        ref = reference[0].lower().split()
        hyp = hypothesis.lower().split()
        
        # Calculate precision for each n-gram
        precisions = []
        
        for i in range(1, n + 1):
            ref_ngrams = []
            hyp_ngrams = []
            
            # Generate n-grams
            for j in range(len(ref) - i + 1):
                ref_ngrams.append(tuple(ref[j:j+i]))
            for j in range(len(hyp) - i + 1):
                hyp_ngrams.append(tuple(hyp[j:j+i]))
            
            # Count matches
            matches = 0
            ref_ngram_counts = {}
            for ngram in ref_ngrams:
                ref_ngram_counts[ngram] = ref_ngram_counts.get(ngram, 0) + 1
            
            hyp_ngram_counts = {}
            for ngram in hyp_ngrams:
                hyp_ngram_counts[ngram] = hyp_ngram_counts.get(ngram, 0) + 1
            
            for ngram in hyp_ngram_counts:
                if ngram in ref_ngram_counts:
                    matches += min(hyp_ngram_counts[ngram], ref_ngram_counts[ngram])
            
            if len(hyp_ngrams) == 0:
                precisions.append(0.0)
            else:
                precisions.append(matches / len(hyp_ngrams))
        
        # Calculate brevity penalty
        if len(hyp) < len(ref):
            bp = np.exp(1 - len(ref) / len(hyp))
        else:
            bp = 1.0
        
        # Calculate BLEU
        if min(precisions) == 0:
            return 0.0
        
        bleu = bp * (np.prod(precisions) ** (1.0 / n))
        return bleu
    
    @staticmethod
    def calculate_rouge_l(reference: str, hypothesis: str) -> float:
        """
        Calculate ROUGE-L score (Longest Common Subsequence)
        
        Returns:
            ROUGE-L F1 score (0.0 to 1.0, higher is better)
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        # Calculate LCS
        n, m = len(ref_words), len(hyp_words)
        lcs = [[0] * (m + 1) for _ in range(n + 1)]
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    lcs[i][j] = lcs[i-1][j-1] + 1
                else:
                    lcs[i][j] = max(lcs[i-1][j], lcs[i][j-1])
        
        lcs_length = lcs[n][m]
        
        if n == 0 or m == 0:
            return 0.0
        
        precision = lcs_length / m
        recall = lcs_length / n
        
        if precision + recall == 0:
            return 0.0
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return f1


class ModelEvaluator:
    """Main model evaluation class"""
    
    def __init__(self):
        self.asr_evaluator = ASREvaluator()
        self.translation_evaluator = TranslationEvaluator()
    
    def evaluate_asr(self, references: List[str], hypotheses: List[str]) -> Dict[str, float]:
        """
        Evaluate ASR model on dataset
        
        Returns:
            Dictionary with metrics
        """
        if len(references) != len(hypotheses):
            raise ValueError("References and hypotheses must have same length")
        
        wers = []
        accuracies = []
        
        for ref, hyp in zip(references, hypotheses):
            wers.append(self.asr_evaluator.calculate_wer(ref, hyp))
            accuracies.append(self.asr_evaluator.calculate_accuracy(ref, hyp))
        
        return {
            'wer': np.mean(wers),
            'wer_std': np.std(wers),
            'accuracy': np.mean(accuracies),
            'accuracy_std': np.std(accuracies)
        }
    
    def evaluate_translation(self, references: List[List[str]], 
                           hypotheses: List[str]) -> Dict[str, float]:
        """
        Evaluate translation model on dataset
        
        Returns:
            Dictionary with metrics
        """
        if len(references) != len(hypotheses):
            raise ValueError("References and hypotheses must have same length")
        
        bleus = []
        rouge_ls = []
        
        for ref_list, hyp in zip(references, hypotheses):
            bleus.append(self.translation_evaluator.calculate_bleu(ref_list, hyp))
            rouge_ls.append(self.translation_evaluator.calculate_rouge_l(ref_list[0], hyp))
        
        return {
            'bleu': np.mean(bleus),
            'bleu_std': np.std(bleus),
            'rouge_l': np.mean(rouge_ls),
            'rouge_l_std': np.std(rouge_ls)
        }

