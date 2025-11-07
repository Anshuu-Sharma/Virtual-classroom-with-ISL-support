"""
Compare ML Translation Model vs Stanford Parser
Shows side-by-side comparison of translation quality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from services.translation_service import get_translation_service, is_ml_model_available
from server import convert_eng_to_isl
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise

def calculate_bleu_simple(reference, hypothesis):
    """Simple BLEU score approximation"""
    ref_words = set(reference.lower().split())
    hyp_words = set(hypothesis.lower().split())
    
    if not ref_words or not hyp_words:
        return 0.0
    
    overlap = len(ref_words & hyp_words)
    return overlap / len(ref_words)

def test_translations():
    """Test and compare ML vs Stanford Parser translations"""
    
    print("="*80)
    print("ML Translation Model vs Stanford Parser Comparison")
    print("="*80)
    
    # Check if ML model is available
    ml_available = is_ml_model_available()
    
    if ml_available:
        print("\n✅ ML Model: LOADED")
        translation_service = get_translation_service()
    else:
        print("\n⚠️  ML Model: NOT LOADED (will only show Stanford Parser results)")
        print("    Train the model first using Kaggle notebook!")
    
    print("="*80)
    
    # Test cases with expected ISL grammar
    test_cases = [
        {
            "english": "hello how are you",
            "expected_isl": "hello you fine how",
            "category": "Greetings"
        },
        {
            "english": "what is your name",
            "expected_isl": "your name what",
            "category": "Questions"
        },
        {
            "english": "i am learning sign language",
            "expected_isl": "i sign language learn",
            "category": "SOV Order"
        },
        {
            "english": "can you help me",
            "expected_isl": "you me help can",
            "category": "Questions"
        },
        {
            "english": "thank you very much",
            "expected_isl": "thank you",
            "category": "Greetings"
        },
        {
            "english": "good morning",
            "expected_isl": "morning good",
            "category": "Greetings"
        },
        {
            "english": "where do you live",
            "expected_isl": "you live where",
            "category": "Questions"
        },
        {
            "english": "she is teaching students",
            "expected_isl": "she student teach",
            "category": "SOV Order"
        },
        {
            "english": "i want to learn",
            "expected_isl": "i learn want",
            "category": "SOV Order"
        },
        {
            "english": "students are studying in class",
            "expected_isl": "student class study",
            "category": "Complex"
        }
    ]
    
    results = []
    total_bleu_ml = 0
    total_bleu_stanford = 0
    
    print("\nComparing translations:\n")
    
    for i, test in enumerate(test_cases, 1):
        english = test["english"]
        expected = test["expected_isl"]
        category = test["category"]
        
        print(f"\n{i}. [{category}]")
        print("-" * 80)
        print(f"English:     {english}")
        print(f"Expected ISL: {expected}")
        
        # Stanford Parser (via convert_eng_to_isl with ML disabled)
        try:
            # Temporarily disable ML to test Stanford
            if ml_available:
                temp_ml_status = translation_service.use_ml_model
                translation_service.use_ml_model = False
            
            stanford_tokens = convert_eng_to_isl(english.capitalize())
            stanford_result = ' '.join(stanford_tokens).lower()
            stanford_bleu = calculate_bleu_simple(expected, stanford_result)
            
            if ml_available:
                translation_service.use_ml_model = temp_ml_status
        except Exception as e:
            stanford_result = f"Error: {str(e)}"
            stanford_bleu = 0.0
        
        print(f"Stanford:    {stanford_result} (BLEU: {stanford_bleu:.2f})")
        total_bleu_stanford += stanford_bleu
        
        # ML Model
        if ml_available:
            try:
                ml_tokens = translation_service.translate_ml(english)
                ml_result = ' '.join(ml_tokens).lower()
                ml_bleu = calculate_bleu_simple(expected, ml_result)
                print(f"ML Model:    {ml_result} (BLEU: {ml_bleu:.2f})")
                total_bleu_ml += ml_bleu
                
                # Winner
                if ml_bleu > stanford_bleu:
                    print("Winner:      🏆 ML Model (better ISL grammar)")
                elif stanford_bleu > ml_bleu:
                    print("Winner:      📚 Stanford Parser")
                else:
                    print("Winner:      🤝 Tie")
            except Exception as e:
                print(f"ML Model:    Error: {str(e)}")
        
        results.append({
            "english": english,
            "expected": expected,
            "stanford": stanford_result,
            "stanford_bleu": stanford_bleu,
            "ml": ml_result if ml_available else "N/A",
            "ml_bleu": ml_bleu if ml_available else 0.0
        })
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    avg_stanford = total_bleu_stanford / len(test_cases)
    print(f"\nStanford Parser Average BLEU: {avg_stanford:.3f}")
    
    if ml_available:
        avg_ml = total_bleu_ml / len(test_cases)
        print(f"ML Model Average BLEU:        {avg_ml:.3f}")
        improvement = ((avg_ml - avg_stanford) / avg_stanford * 100) if avg_stanford > 0 else 0
        print(f"\nImprovement: {improvement:+.1f}%")
        
        if improvement > 10:
            print("\n✅ ML model shows >10% improvement! Quality perfection achieved!")
        elif improvement > 0:
            print("\n✅ ML model is better, but <10% improvement. Consider more training.")
        else:
            print("\n⚠️  ML model needs improvement. Check training data quality.")
    else:
        print("\n⚠️  ML model not loaded. Train it first to see comparison!")
    
    print("="*80)
    
    return results

def main():
    """Main function"""
    try:
        results = test_translations()
        
        print("\nDetailed results saved. You can:")
        print("1. Review translations above")
        print("2. Open evaluation dashboard: http://localhost:5001/ml-comparison")
        print("3. Test more sentences in your browser")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

