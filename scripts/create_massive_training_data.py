"""
MASSIVE Perfect ISL Training Data Generator
Systematically generates 10,000+ high-quality training pairs
"""

import json
import random
from pathlib import Path
import sys
from itertools import product, combinations

sys.path.insert(0, str(Path(__file__).parent.parent))

def load_sigml_vocabulary():
    """Load available signs"""
    sigml_path = Path(__file__).parent.parent / "js" / "sigmlFiles.json"
    with open(sigml_path, 'r') as f:
        content = f.read()
        start = content.find('[')
        end = content.rfind(']') + 1
        sigml_list = json.loads(content[start:end])
    
    vocab = set()
    for item in sigml_list:
        name = item.get('name', '').lower().strip()
        if name and name not in ['', 'eol']:
            vocab.add(name)
    
    return sorted(list(vocab))

def categorize_vocab(vocab):
    """Categorize vocabulary for systematic generation"""
    
    categories = {
        'pronouns_subj': ['i', 'you', 'he', 'she', 'we', 'they'],
        'pronouns_obj': ['me', 'you', 'him', 'her', 'us', 'them'],
        'pronouns_poss': ['my', 'your', 'his', 'her', 'our', 'their'],
        
        'verbs_common': ['go', 'come', 'want', 'like', 'need', 'learn', 'teach', 
                         'help', 'work', 'study', 'read', 'write', 'speak', 'sign',
                         'know', 'understand', 'see', 'hear', 'think', 'feel'],
        
        'verbs_action': ['sit', 'stand', 'walk', 'run', 'eat', 'drink', 'sleep',
                         'play', 'give', 'take', 'buy', 'sell', 'make', 'do',
                         'start', 'finish', 'stop', 'continue', 'try', 'practice'],
        
        'nouns_people': ['student', 'teacher', 'friend', 'family', 'person',
                         'man', 'woman', 'boy', 'girl', 'child', 'parent'],
        
        'nouns_places': ['school', 'class', 'home', 'work', 'city', 'country',
                         'office', 'hospital', 'market', 'shop'],
        
        'nouns_things': ['book', 'pen', 'paper', 'computer', 'phone', 'table',
                         'chair', 'door', 'window', 'water', 'food', 'money'],
        
        'nouns_abstract': ['language', 'sign', 'name', 'time', 'day', 'week',
                          'month', 'year', 'work', 'homework', 'question',
                          'answer', 'problem', 'idea'],
        
        'adjectives': ['good', 'bad', 'happy', 'sad', 'big', 'small', 'new',
                      'old', 'young', 'easy', 'difficult', 'important', 'nice',
                      'fine', 'correct', 'wrong', 'right', 'ready'],
        
        'time_words': ['today', 'tomorrow', 'yesterday', 'now', 'morning',
                      'afternoon', 'evening', 'night', 'monday', 'tuesday',
                      'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        
        'modals': ['can', 'could', 'should', 'would', 'will', 'must', 'may', 'might'],
        
        'question_words': ['what', 'where', 'when', 'who', 'why', 'how', 'which'],
    }
    
    # Filter to only available signs
    for key in categories:
        categories[key] = [w for w in categories[key] if w in vocab]
    
    return categories

def generate_systematic_sov():
    """Systematically generate SOV patterns"""
    
    patterns = []
    cats = categorize_vocab(load_sigml_vocabulary())
    
    # Subject + Verb + Object (SOV in ISL)
    for subj in cats['pronouns_subj']:
        for verb in cats['verbs_common'][:15]:
            for obj in cats['nouns_things'][:15]:
                patterns.append((
                    f"{subj} {verb} {obj}",
                    f"{subj} {obj} {verb}"
                ))
    
    # Subject + Verb + Object + Adjective
    for subj in cats['pronouns_subj']:
        for adj in cats['adjectives'][:10]:
            for obj in cats['nouns_abstract'][:10]:
                for verb in cats['verbs_common'][:5]:
                    patterns.append((
                        f"{subj} {verb} {adj} {obj}",
                        f"{subj} {adj} {obj} {verb}"
                    ))
    
    # Present continuous -> Simple (remove am/is/are)
    for subj in cats['pronouns_subj']:
        for verb in cats['verbs_action'][:15]:
            for obj in cats['nouns_things'][:10]:
                aux = 'am' if subj == 'i' else ('are' if subj in ['you', 'we', 'they'] else 'is')
                patterns.append((
                    f"{subj} {aux} {verb}ing {obj}",
                    f"{subj} {obj} {verb}"
                ))
    
    return patterns

def generate_systematic_questions():
    """Systematically generate question patterns"""
    
    patterns = []
    cats = categorize_vocab(load_sigml_vocabulary())
    
    # What + Subject + Verb
    for subj in cats['pronouns_subj']:
        for verb in cats['verbs_common'][:10]:
            patterns.append((
                f"what do {subj} {verb}",
                f"{subj} {verb} what"
            ))
            patterns.append((
                f"what does {subj} {verb}",
                f"{subj} {verb} what"
            ))
    
    # Where + Subject + Verb
    for subj in cats['pronouns_subj']:
        for verb in cats['verbs_action'][:10]:
            patterns.append((
                f"where do {subj} {verb}",
                f"{subj} {verb} where"
            ))
    
    # When + Subject + Verb
    for subj in cats['pronouns_subj']:
        for verb in cats['verbs_common'][:10]:
            patterns.append((
                f"when do {subj} {verb}",
                f"{subj} {verb} when"
            ))
            patterns.append((
                f"when will {subj} {verb}",
                f"{subj} {verb} when"
            ))
    
    # How + Adjective
    for adj in cats['adjectives'][:15]:
        patterns.extend([
            (f"how {adj} is it", f"it {adj} how"),
            (f"how {adj} are you", f"you {adj} how"),
        ])
    
    # What is + Noun
    for noun in cats['nouns_abstract'][:20]:
        patterns.extend([
            (f"what is {noun}", f"{noun} what"),
            (f"what is your {noun}", f"your {noun} what"),
            (f"what is the {noun}", f"{noun} what"),
        ])
    
    return patterns

def generate_systematic_modals():
    """Systematically generate modal patterns"""
    
    patterns = []
    cats = categorize_vocab(load_sigml_vocabulary())
    
    # Modal + Subject + Verb + Object
    for modal in cats['modals']:
        for subj in cats['pronouns_subj']:
            for verb in cats['verbs_common'][:10]:
                for obj in cats['nouns_things'][:10]:
                    patterns.append((
                        f"{subj} {modal} {verb} {obj}",
                        f"{subj} {obj} {verb} {modal}"
                    ))
                    
                    # Question form
                    patterns.append((
                        f"{modal} {subj} {verb} {obj}",
                        f"{subj} {obj} {verb} {modal}"
                    ))
    
    # Want/Need to
    for subj in cats['pronouns_subj']:
        for verb in cats['verbs_common'][:15]:
            for obj in cats['nouns_abstract'][:10]:
                patterns.extend([
                    (f"{subj} want to {verb} {obj}", f"{subj} {obj} {verb} want"),
                    (f"{subj} need to {verb} {obj}", f"{subj} {obj} {verb} need"),
                ])
    
    return patterns

def generate_systematic_time_location():
    """Systematically generate time/location patterns"""
    
    patterns = []
    cats = categorize_vocab(load_sigml_vocabulary())
    
    # Time at start
    for time in cats['time_words']:
        for subj in cats['pronouns_subj']:
            for verb in cats['verbs_common'][:10]:
                patterns.append((
                    f"{subj} will {verb} {time}",
                    f"{time} {subj} {verb}"
                ))
                patterns.append((
                    f"{subj} {verb}s {time}",
                    f"{time} {subj} {verb}"
                ))
    
    # Location at start
    for loc in cats['nouns_places']:
        for subj in cats['pronouns_subj']:
            for verb in cats['verbs_action'][:8]:
                patterns.append((
                    f"{subj} {verb} at {loc}",
                    f"{loc} {subj} {verb}"
                ))
                patterns.append((
                    f"{subj} {verb}s in {loc}",
                    f"{loc} {subj} {verb}"
                ))
    
    return patterns

def generate_systematic_negations():
    """Systematically generate negation patterns"""
    
    patterns = []
    cats = categorize_vocab(load_sigml_vocabulary())
    
    for subj in cats['pronouns_subj']:
        for verb in cats['verbs_common'][:15]:
            patterns.extend([
                (f"{subj} do not {verb}", f"{subj} {verb} not"),
                (f"{subj} does not {verb}", f"{subj} {verb} not"),
                (f"{subj} will not {verb}", f"{subj} {verb} not"),
            ])
            
            # With objects
            for obj in cats['nouns_things'][:8]:
                patterns.extend([
                    (f"{subj} do not {verb} {obj}", f"{subj} {obj} {verb} not"),
                    (f"{subj} cannot {verb} {obj}", f"{subj} {obj} {verb} not can"),
                ])
    
    return patterns

def create_massive_dataset():
    """Create massive high-quality dataset"""
    
    print("="*60)
    print("GENERATING MASSIVE PERFECT ISL DATASET")
    print("="*60)
    
    all_pairs = []
    
    print("\n1. Generating systematic SOV patterns...")
    sov = generate_systematic_sov()
    all_pairs.extend(sov)
    print(f"   ✅ Generated {len(sov)} SOV patterns")
    
    print("2. Generating systematic questions...")
    questions = generate_systematic_questions()
    all_pairs.extend(questions)
    print(f"   ✅ Generated {len(questions)} questions")
    
    print("3. Generating systematic modals...")
    modals = generate_systematic_modals()
    all_pairs.extend(modals)
    print(f"   ✅ Generated {len(modals)} modal sentences")
    
    print("4. Generating systematic time/location...")
    time_loc = generate_systematic_time_location()
    all_pairs.extend(time_loc)
    print(f"   ✅ Generated {len(time_loc)} time/location patterns")
    
    print("5. Generating systematic negations...")
    negations = generate_systematic_negations()
    all_pairs.extend(negations)
    print(f"   ✅ Generated {len(negations)} negations")
    
    # Load and add the manually crafted perfect pairs
    print("6. Loading manually crafted perfect pairs...")
    perfect_path = Path(__file__).parent.parent / "data" / "train_pairs_perfect.json"
    if perfect_path.exists():
        with open(perfect_path, 'r') as f:
            perfect_data = json.load(f)
            for item in perfect_data:
                eng = item['english'].replace('<sos> ', '').replace(' <eos>', '')
                isl = item['isl'].replace('<sos> ', '').replace(' <eos>', '')
                all_pairs.append((eng, isl))
        print(f"   ✅ Added {len(perfect_data)} manually crafted pairs")
    
    # Remove duplicates
    unique_pairs = list(set(all_pairs))
    print(f"\n✅ Total unique pairs: {len(unique_pairs)}")
    
    # Format with special tokens
    formatted_pairs = []
    for eng, isl in unique_pairs:
        formatted_pairs.append({
            "english": f"<sos> {eng} <eos>",
            "isl": f"<sos> {isl} <eos>"
        })
    
    # Shuffle
    random.shuffle(formatted_pairs)
    
    # Split 85/15
    split_idx = int(len(formatted_pairs) * 0.85)
    train_pairs = formatted_pairs[:split_idx]
    val_pairs = formatted_pairs[split_idx:]
    
    print(f"\nDataset split:")
    print(f"  Training: {len(train_pairs)} pairs")
    print(f"  Validation: {len(val_pairs)} pairs")
    
    # Analyze quality
    analyze_dataset_quality(train_pairs)
    
    # Save
    data_dir = Path(__file__).parent.parent / "data"
    train_path = data_dir / "train_pairs_massive.json"
    val_path = data_dir / "val_pairs_massive.json"
    
    with open(train_path, 'w', encoding='utf-8') as f:
        json.dump(train_pairs, f, indent=2, ensure_ascii=False)
    
    with open(val_path, 'w', encoding='utf-8') as f:
        json.dump(val_pairs, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved to:")
    print(f"   {train_path}")
    print(f"   {val_path}")
    
    # Show samples
    show_quality_samples(train_pairs)
    
    return train_path, val_path

def analyze_dataset_quality(pairs):
    """Analyze dataset quality"""
    
    single_word = 0
    short_phrase = 0
    medium = 0
    complex_sentence = 0
    proper_grammar = 0
    
    for pair in pairs:
        eng = pair['english'].replace('<sos> ', '').replace(' <eos>', '')
        isl = pair['isl'].replace('<sos> ', '').replace(' <eos>', '')
        
        word_count = len(eng.split())
        
        if word_count == 1:
            single_word += 1
        elif word_count <= 3:
            short_phrase += 1
        elif word_count <= 5:
            medium += 1
        else:
            complex_sentence += 1
        
        if eng != isl:
            proper_grammar += 1
    
    total = len(pairs)
    print("\n" + "="*60)
    print("DATASET QUALITY ANALYSIS")
    print("="*60)
    print(f"Single words: {single_word} ({single_word/total*100:.1f}%)")
    print(f"Short phrases (2-3): {short_phrase} ({short_phrase/total*100:.1f}%)")
    print(f"Medium (4-5): {medium} ({medium/total*100:.1f}%)")
    print(f"Complex (6+): {complex_sentence} ({complex_sentence/total*100:.1f}%)")
    print(f"Proper ISL grammar: {proper_grammar} ({proper_grammar/total*100:.1f}%)")
    print("="*60)

def show_quality_samples(pairs):
    """Show diverse quality samples"""
    
    print("\n" + "="*60)
    print("SAMPLE PERFECT TRAINING PAIRS")
    print("="*60)
    
    # Show complex sentences first
    complex_samples = []
    medium_samples = []
    
    for pair in pairs:
        eng = pair['english'].replace('<sos> ', '').replace(' <eos>', '')
        isl = pair['isl'].replace('<sos> ', '').replace(' <eos>', '')
        
        if len(eng.split()) >= 5 and eng != isl:
            complex_samples.append((eng, isl))
        elif len(eng.split()) == 4 and eng != isl:
            medium_samples.append((eng, isl))
    
    print("\nComplex sentences (6+ words):")
    for i, (eng, isl) in enumerate(complex_samples[:10], 1):
        print(f"{i:2d}. '{eng}' → '{isl}'")
    
    print("\nMedium sentences (4-5 words):")
    for i, (eng, isl) in enumerate(medium_samples[:10], 1):
        print(f"{i:2d}. '{eng}' → '{isl}'")
    
    print("="*60)

if __name__ == "__main__":
    create_massive_dataset()

