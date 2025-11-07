"""
Enhanced Training Data Generator for ISL Translation
Creates high-quality training pairs with proper ISL grammar rules
"""

import json
import random
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_sigml_vocabulary():
    """Load available signs from sigmlFiles.json"""
    sigml_path = Path(__file__).parent.parent / "js" / "sigmlFiles.json"
    
    with open(sigml_path, 'r') as f:
        content = f.read()
        # Extract JSON array
        start = content.find('[')
        end = content.rfind(']') + 1
        sigml_list = json.loads(content[start:end])
    
    # Extract vocabulary (sign names)
    vocab = set()
    for item in sigml_list:
        name = item.get('name', '').lower().strip()
        if name and name not in ['', 'eol']:
            vocab.add(name)
    
    print(f"Loaded {len(vocab)} signs from SiGML vocabulary")
    return sorted(list(vocab))

def apply_isl_grammar(english_words):
    """
    Apply ISL grammar rules to English sentence
    
    ISL Grammar Rules:
    1. SOV word order (Subject-Object-Verb)
    2. Remove articles (a, an, the)
    3. Remove auxiliary verbs (am, is, are, was, were, have, has, had, will, would, should, could)
    4. Remove unnecessary prepositions
    5. WH-questions at end
    6. Remove "to" before verbs
    7. Topic-comment structure
    """
    
    # Articles to remove
    articles = {'a', 'an', 'the'}
    
    # Auxiliary verbs to remove
    auxiliaries = {'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                   'have', 'has', 'had', 'do', 'does', 'did',
                   'will', 'would', 'shall', 'should', 'can', 'could', 
                   'may', 'might', 'must'}
    
    # Prepositions that can be removed in ISL
    removable_preps = {'to', 'of', 'for', 'at', 'in', 'on', 'with'}
    
    # WH-question words
    wh_words = {'what', 'where', 'when', 'who', 'why', 'how', 'which'}
    
    isl_words = []
    wh_question = None
    
    for word in english_words:
        word_lower = word.lower()
        
        # Save WH-question word for end
        if word_lower in wh_words:
            wh_question = word_lower
            continue
        
        # Skip articles
        if word_lower in articles:
            continue
        
        # Skip auxiliaries
        if word_lower in auxiliaries:
            continue
        
        # Skip some prepositions
        if word_lower in removable_preps:
            continue
        
        # Keep the word
        isl_words.append(word_lower)
    
    # Add WH-question at end (ISL structure)
    if wh_question:
        isl_words.append(wh_question)
    
    return isl_words

def generate_grammar_patterns(vocab):
    """Generate diverse sentence patterns with ISL grammar"""
    
    # Filter vocabulary for specific word types
    pronouns = [w for w in vocab if w in ['i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'our', 'their']]
    verbs = [w for w in vocab if w in ['go', 'come', 'want', 'like', 'need', 'learn', 'teach', 'help', 'work', 'study', 'read', 'write', 'play', 'eat', 'drink', 'sleep', 'walk', 'run', 'sit', 'stand', 'give', 'take', 'see', 'hear', 'feel', 'think', 'know', 'understand', 'speak', 'sign']]
    nouns = [w for w in vocab if w in ['book', 'student', 'teacher', 'class', 'school', 'home', 'work', 'language', 'sign', 'name', 'time', 'day', 'week', 'month', 'year', 'water', 'food', 'friend', 'family', 'person', 'thing', 'place']]
    adjectives = [w for w in vocab if w in ['good', 'bad', 'happy', 'sad', 'big', 'small', 'new', 'old', 'young', 'beautiful', 'easy', 'difficult', 'important', 'nice', 'fine']]
    
    patterns = []
    
    # Pattern 1: Simple greetings and common phrases
    greetings = [
        ("hello", "hello"),
        ("good morning", "morning good"),
        ("good night", "night good"),
        ("thank you", "thank you"),
        ("thank you very much", "thank you"),
        ("you are welcome", "welcome"),
        ("how are you", "you fine how"),
        ("i am fine", "i fine"),
        ("nice to meet you", "you meet nice"),
        ("see you later", "you see later"),
        ("goodbye", "goodbye"),
    ]
    patterns.extend(greetings)
    
    # Pattern 2: Questions (WH-word at end in ISL)
    questions = [
        ("what is your name", "your name what"),
        ("where do you live", "you live where"),
        ("when will you come", "you come when"),
        ("who is your teacher", "your teacher who"),
        ("why are you sad", "you sad why"),
        ("how are you feeling", "you feel how"),
        ("what do you want", "you want what"),
        ("where is the book", "book where"),
        ("when is class", "class when"),
        ("who can help me", "me help who can"),
    ]
    patterns.extend(questions)
    
    # Pattern 3: SOV structure (Subject-Object-Verb)
    sov_sentences = [
        ("i am learning sign language", "i sign language learn"),
        ("she is teaching students", "she student teach"),
        ("he likes reading books", "he book read like"),
        ("we want to help you", "we you help want"),
        ("they are studying english", "they english study"),
        ("i need your help", "i your help need"),
        ("you can speak sign language", "you sign language speak can"),
        ("students learn new things", "student new thing learn"),
        ("teacher teaches sign language", "teacher sign language teach"),
        ("i like to eat food", "i food eat like"),
    ]
    patterns.extend(sov_sentences)
    
    # Pattern 4: Complex sentences with ISL grammar
    complex_sentences = [
        ("i want to learn sign language", "i sign language learn want"),
        ("can you help me please", "you me help can please"),
        ("students are studying in class", "student class study"),
        ("i am going to school", "i school go"),
        ("he will come tomorrow", "he tomorrow come"),
        ("she has finished her work", "she work finish"),
        ("we should study together", "we together study"),
        ("they can sign very well", "they sign good can"),
        ("i need to go home", "i home go need"),
        ("you must learn this", "you this learn must"),
    ]
    patterns.extend(complex_sentences)
    
    # Pattern 5: Statements without auxiliaries
    statements = [
        ("i am a student", "i student"),
        ("she is a teacher", "she teacher"),
        ("we are friends", "we friend"),
        ("this is important", "this important"),
        ("that is correct", "that correct"),
        ("it is easy", "it easy"),
        ("they are happy", "they happy"),
        ("i am busy", "i busy"),
        ("you are right", "you right"),
        ("he is young", "he young"),
    ]
    patterns.extend(statements)
    
    # Pattern 6: Negations
    negations = [
        ("i do not understand", "i understand not"),
        ("he cannot come", "he come not can"),
        ("she does not know", "she know not"),
        ("we will not go", "we go not"),
        ("they are not ready", "they ready not"),
        ("i did not see", "i see not"),
        ("you should not worry", "you worry not"),
    ]
    patterns.extend(negations)
    
    # Pattern 7: Time expressions (time at start in ISL)
    time_expressions = [
        ("i will see you tomorrow", "tomorrow i you see"),
        ("we studied yesterday", "yesterday we study"),
        ("class starts in the morning", "morning class start"),
        ("he comes every day", "every day he come"),
        ("they work at night", "night they work"),
        ("i went last week", "last week i go"),
        ("you can come next month", "next month you come can"),
    ]
    patterns.extend(time_expressions)
    
    # Pattern 8: Location expressions (location at start)
    location_expressions = [
        ("i study at school", "school i study"),
        ("she works at home", "home she work"),
        ("we meet in class", "class we meet"),
        ("they live in city", "city they live"),
        ("book is on table", "table book"),
    ]
    patterns.extend(location_expressions)
    
    return patterns

def generate_word_variations(vocab):
    """Generate single word variations (existing data augmentation)"""
    variations = []
    
    for word in vocab:
        # Add word as-is
        variations.append((word, word))
    
    return variations

def create_enhanced_dataset():
    """Create enhanced training dataset"""
    
    print("="*60)
    print("Creating Enhanced ISL Training Dataset")
    print("="*60)
    
    # Load vocabulary
    vocab = load_sigml_vocabulary()
    
    # Generate training pairs
    print("\nGenerating training pairs with ISL grammar...")
    
    # Get grammar-based patterns
    grammar_pairs = generate_grammar_patterns(vocab)
    print(f"Generated {len(grammar_pairs)} grammar-based sentence pairs")
    
    # Get word variations (for vocabulary coverage)
    word_pairs = generate_word_variations(vocab)
    print(f"Generated {len(word_pairs)} vocabulary word pairs")
    
    # Combine all pairs
    all_pairs = grammar_pairs + word_pairs
    
    # Remove duplicates
    unique_pairs = list(set(all_pairs))
    print(f"Total unique pairs: {len(unique_pairs)}")
    
    # Format with special tokens
    formatted_pairs = []
    for eng, isl in unique_pairs:
        formatted_pairs.append({
            "english": f"<sos> {eng} <eos>",
            "isl": f"<sos> {isl} <eos>"
        })
    
    # Shuffle
    random.shuffle(formatted_pairs)
    
    # Split into train/val (80/20)
    split_idx = int(len(formatted_pairs) * 0.8)
    train_pairs = formatted_pairs[:split_idx]
    val_pairs = formatted_pairs[split_idx:]
    
    print(f"\nDataset split:")
    print(f"  Training pairs: {len(train_pairs)}")
    print(f"  Validation pairs: {len(val_pairs)}")
    
    # Save files
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    train_path = data_dir / "train_pairs_enhanced.json"
    val_path = data_dir / "val_pairs_enhanced.json"
    
    with open(train_path, 'w', encoding='utf-8') as f:
        json.dump(train_pairs, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved training data: {train_path}")
    
    with open(val_path, 'w', encoding='utf-8') as f:
        json.dump(val_pairs, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved validation data: {val_path}")
    
    # Show sample pairs
    print("\n" + "="*60)
    print("Sample Enhanced Pairs (English → ISL)")
    print("="*60)
    for i, pair in enumerate(train_pairs[:10], 1):
        eng = pair['english'].replace('<sos> ', '').replace(' <eos>', '')
        isl = pair['isl'].replace('<sos> ', '').replace(' <eos>', '')
        print(f"{i:2d}. '{eng}' → '{isl}'")
    
    print("\n" + "="*60)
    print("✅ Enhanced training data created successfully!")
    print("="*60)
    
    return train_path, val_path

if __name__ == "__main__":
    create_enhanced_dataset()

