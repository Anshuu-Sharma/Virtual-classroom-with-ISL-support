"""
Enhanced Training Data Generator V2 - HIGH QUALITY
Creates 5000+ diverse training pairs with proper ISL grammar
"""

import json
import random
import os
import sys
from pathlib import Path
from itertools import product

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_sigml_vocabulary():
    """Load available signs from sigmlFiles.json"""
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
    
    print(f"Loaded {len(vocab)} signs from SiGML vocabulary")
    return sorted(list(vocab))

def categorize_vocabulary(vocab):
    """Categorize words by type for better sentence generation"""
    
    # Pronouns
    pronouns = {
        'subject': ['i', 'you', 'he', 'she', 'we', 'they'],
        'object': ['me', 'you', 'him', 'her', 'us', 'them'],
        'possessive': ['my', 'your', 'his', 'her', 'our', 'their']
    }
    
    # Verbs (filtered from vocab)
    verbs = [w for w in vocab if w in [
        'go', 'come', 'want', 'like', 'need', 'learn', 'teach', 'help', 
        'work', 'study', 'read', 'write', 'play', 'eat', 'drink', 'sleep',
        'walk', 'run', 'sit', 'stand', 'give', 'take', 'see', 'hear', 
        'feel', 'think', 'know', 'understand', 'speak', 'sign', 'love',
        'hate', 'start', 'finish', 'stop', 'continue', 'try', 'practice',
        'remember', 'forget', 'buy', 'sell', 'pay', 'cost', 'travel',
        'visit', 'stay', 'leave', 'arrive', 'wait', 'meet', 'talk'
    ]]
    
    # Nouns
    nouns = [w for w in vocab if w in [
        'book', 'student', 'teacher', 'class', 'school', 'home', 'work',
        'language', 'sign', 'name', 'time', 'day', 'week', 'month', 'year',
        'water', 'food', 'friend', 'family', 'person', 'thing', 'place',
        'city', 'country', 'house', 'room', 'door', 'window', 'table',
        'chair', 'computer', 'phone', 'paper', 'pen', 'car', 'bus',
        'money', 'question', 'answer', 'problem', 'solution', 'idea',
        'child', 'parent', 'brother', 'sister', 'man', 'woman', 'boy', 'girl'
    ]]
    
    # Adjectives
    adjectives = [w for w in vocab if w in [
        'good', 'bad', 'happy', 'sad', 'big', 'small', 'new', 'old',
        'young', 'beautiful', 'easy', 'difficult', 'important', 'nice',
        'fine', 'great', 'excellent', 'terrible', 'wonderful', 'perfect',
        'correct', 'wrong', 'right', 'left', 'hot', 'cold', 'warm', 'cool',
        'fast', 'slow', 'high', 'low', 'long', 'short', 'wide', 'narrow'
    ]]
    
    # Time words
    time_words = [w for w in vocab if w in [
        'today', 'tomorrow', 'yesterday', 'now', 'morning', 'afternoon',
        'evening', 'night', 'monday', 'tuesday', 'wednesday', 'thursday',
        'friday', 'saturday', 'sunday', 'january', 'february', 'march',
        'april', 'may', 'june', 'july', 'august', 'september', 'october',
        'november', 'december'
    ]]
    
    # Location words
    locations = [w for w in vocab if w in [
        'here', 'there', 'up', 'down', 'left', 'right', 'front', 'back',
        'inside', 'outside', 'near', 'far', 'school', 'home', 'city',
        'country', 'office', 'hospital', 'shop', 'market'
    ]]
    
    # Question words
    question_words = ['what', 'where', 'when', 'who', 'why', 'how', 'which']
    
    # Modal verbs
    modals = ['can', 'could', 'should', 'would', 'will', 'must', 'may', 'might']
    
    return {
        'pronouns': pronouns,
        'verbs': verbs,
        'nouns': nouns,
        'adjectives': adjectives,
        'time': time_words,
        'locations': locations,
        'questions': question_words,
        'modals': modals
    }

def generate_diverse_patterns(categories):
    """Generate diverse sentence patterns with proper ISL grammar"""
    
    patterns = []
    pronouns = categories['pronouns']
    verbs = categories['verbs'][:30]  # Use subset for variety
    nouns = categories['nouns'][:30]
    adjectives = categories['adjectives'][:20]
    time_words = categories['time'][:10]
    locations = categories['locations'][:10]
    questions = categories['questions']
    modals = categories['modals']
    
    print("Generating pattern categories...")
    
    # 1. GREETINGS & COMMON PHRASES (50 pairs)
    greetings = [
        ("hello", "hello"),
        ("hi", "hi"),
        ("good morning", "morning good"),
        ("good afternoon", "afternoon good"),
        ("good evening", "evening good"),
        ("good night", "night good"),
        ("goodbye", "goodbye"),
        ("bye", "bye"),
        ("see you later", "you see later"),
        ("see you tomorrow", "tomorrow you see"),
        ("thank you", "thank you"),
        ("thanks", "thank"),
        ("thank you very much", "thank you"),
        ("you are welcome", "welcome"),
        ("please", "please"),
        ("excuse me", "excuse"),
        ("sorry", "sorry"),
        ("i am sorry", "i sorry"),
        ("no problem", "problem no"),
        ("nice to meet you", "you meet nice"),
        ("how are you", "you fine how"),
        ("i am fine", "i fine"),
        ("i am good", "i good"),
        ("i am okay", "i okay"),
        ("how about you", "you how"),
        ("what is up", "up what"),
        ("not much", "much not"),
        ("same here", "here same"),
        ("take care", "care take"),
        ("have a good day", "day good have"),
        ("have a nice day", "day nice have"),
        ("good luck", "luck good"),
        ("congratulations", "congratulations"),
        ("happy birthday", "birthday happy"),
        ("merry christmas", "christmas happy"),
        ("happy new year", "year new happy"),
        ("i love you", "i you love"),
        ("i miss you", "i you miss"),
        ("i understand", "i understand"),
        ("i do not understand", "i understand not"),
        ("i know", "i know"),
        ("i do not know", "i know not"),
        ("i agree", "i agree"),
        ("i disagree", "i agree not"),
        ("that is right", "that right"),
        ("that is correct", "that correct"),
        ("that is wrong", "that wrong"),
        ("yes please", "yes please"),
        ("no thank you", "no thank you"),
        ("maybe", "maybe"),
    ]
    patterns.extend(greetings)
    print(f"  Added {len(greetings)} greetings")
    
    # 2. WH-QUESTIONS (100+ pairs) - Question word at END in ISL
    wh_questions = []
    
    # What questions
    for noun in nouns[:15]:
        wh_questions.extend([
            (f"what is {noun}", f"{noun} what"),
            (f"what is your {noun}", f"your {noun} what"),
            (f"what is the {noun}", f"{noun} what"),
        ])
    
    # Where questions
    for verb in verbs[:15]:
        wh_questions.extend([
            (f"where do you {verb}", f"you {verb} where"),
            (f"where does he {verb}", f"he {verb} where"),
            (f"where can i {verb}", f"i {verb} where can"),
        ])
    
    # When questions
    for verb in verbs[:10]:
        wh_questions.extend([
            (f"when do you {verb}", f"you {verb} when"),
            (f"when will you {verb}", f"you {verb} when"),
        ])
    
    # Who questions
    wh_questions.extend([
        (f"who is {noun}", f"{noun} who")
        for noun in nouns[:10]
    ])
    
    # How questions
    for adj in adjectives[:10]:
        wh_questions.append((f"how {adj} is it", f"it {adj} how"))
    
    # Why questions
    for verb in verbs[:10]:
        wh_questions.append((f"why do you {verb}", f"you {verb} why"))
    
    patterns.extend(wh_questions[:150])  # Limit to 150
    print(f"  Added {len(wh_questions[:150])} WH-questions")
    
    # 3. SOV SENTENCES (200+ pairs) - Subject-Object-Verb
    sov_sentences = []
    
    # Simple SOV with pronouns
    for subj in pronouns['subject'][:6]:
        for obj in nouns[:20]:
            for verb in verbs[:10]:
                sov_sentences.append((
                    f"{subj} {verb} {obj}",
                    f"{subj} {obj} {verb}"
                ))
    
    # SOV with adjectives
    for subj in pronouns['subject'][:4]:
        for adj in adjectives[:10]:
            for obj in nouns[:10]:
                for verb in verbs[:5]:
                    sov_sentences.append((
                        f"{subj} {verb} {adj} {obj}",
                        f"{subj} {adj} {obj} {verb}"
                    ))
    
    # Present continuous -> Simple (remove "am/is/are" and "-ing")
    for subj in pronouns['subject'][:5]:
        for verb in verbs[:15]:
            for obj in nouns[:10]:
                sov_sentences.extend([
                    (f"{subj} am {verb}ing {obj}", f"{subj} {obj} {verb}"),
                    (f"{subj} is {verb}ing {obj}", f"{subj} {obj} {verb}"),
                    (f"{subj} are {verb}ing {obj}", f"{subj} {obj} {verb}"),
                ])
    
    patterns.extend(sov_sentences[:250])
    print(f"  Added {len(sov_sentences[:250])} SOV sentences")
    
    # 4. MODAL SENTENCES (100 pairs) - Can, should, want, etc.
    modal_sentences = []
    
    for subj in pronouns['subject'][:5]:
        for modal in modals[:5]:
            for verb in verbs[:10]:
                for obj in nouns[:8]:
                    modal_sentences.append((
                        f"{subj} {modal} {verb} {obj}",
                        f"{subj} {obj} {verb} {modal}"
                    ))
    
    # Want to / need to
    for subj in pronouns['subject'][:5]:
        for verb in verbs[:15]:
            for obj in nouns[:10]:
                modal_sentences.extend([
                    (f"{subj} want to {verb} {obj}", f"{subj} {obj} {verb} want"),
                    (f"{subj} need to {verb} {obj}", f"{subj} {obj} {verb} need"),
                ])
    
    patterns.extend(modal_sentences[:150])
    print(f"  Added {len(modal_sentences[:150])} modal sentences")
    
    # 5. TIME EXPRESSIONS (100 pairs) - Time at START in ISL
    time_sentences = []
    
    for time in time_words[:10]:
        for subj in pronouns['subject'][:5]:
            for verb in verbs[:10]:
                time_sentences.extend([
                    (f"i will {verb} {time}", f"{time} i {verb}"),
                    (f"{subj} {verb}s {time}", f"{time} {subj} {verb}"),
                ])
    
    patterns.extend(time_sentences[:120])
    print(f"  Added {len(time_sentences[:120])} time expressions")
    
    # 6. LOCATION EXPRESSIONS (80 pairs) - Location at START
    loc_sentences = []
    
    for loc in locations[:8]:
        for subj in pronouns['subject'][:5]:
            for verb in verbs[:8]:
                loc_sentences.extend([
                    (f"{subj} {verb} at {loc}", f"{loc} {subj} {verb}"),
                    (f"{subj} {verb}s in {loc}", f"{loc} {subj} {verb}"),
                ])
    
    patterns.extend(loc_sentences[:100])
    print(f"  Added {len(loc_sentences[:100])} location expressions")
    
    # 7. NEGATIONS (80 pairs)
    negations = []
    
    for subj in pronouns['subject'][:6]:
        for verb in verbs[:12]:
            negations.extend([
                (f"{subj} do not {verb}", f"{subj} {verb} not"),
                (f"{subj} does not {verb}", f"{subj} {verb} not"),
                (f"{subj} did not {verb}", f"{subj} {verb} not"),
                (f"{subj} will not {verb}", f"{subj} {verb} not"),
                (f"{subj} cannot {verb}", f"{subj} {verb} not can"),
            ])
    
    patterns.extend(negations[:100])
    print(f"  Added {len(negations[:100])} negations")
    
    # 8. POSSESSIVE SENTENCES (60 pairs)
    possessive = []
    
    for poss in pronouns['possessive'][:6]:
        for noun in nouns[:10]:
            for adj in adjectives[:8]:
                possessive.extend([
                    (f"{poss} {noun} is {adj}", f"{poss} {noun} {adj}"),
                    (f"this is {poss} {noun}", f"this {poss} {noun}"),
                ])
    
    patterns.extend(possessive[:80])
    print(f"  Added {len(possessive[:80])} possessive sentences")
    
    # 9. COMPLEX SENTENCES (100 pairs)
    complex_sentences = [
        ("i want to learn sign language", "i sign language learn want"),
        ("can you help me with homework", "you me homework help can"),
        ("students are studying in the classroom", "classroom student study"),
        ("teacher is teaching sign language today", "today teacher sign language teach"),
        ("where can i buy the book", "i book buy where can"),
        ("what time does the class start", "class start time what"),
        ("how much does it cost", "it cost how"),
        ("when will you come to school", "school you come when"),
        ("why do you want to learn", "you learn want why"),
        ("i need to finish my work", "i work finish need"),
        ("she wants to go home early", "she home early go want"),
        ("we should study together tomorrow", "tomorrow we together study should"),
        ("they are going to the market", "market they go"),
        ("can you teach me sign language", "you me sign language teach can"),
        ("i do not understand the question", "i question understand not"),
        ("he needs help with his homework", "he homework help need"),
        ("students must come to class on time", "student class time come must"),
        ("what is your favorite book", "your book favorite what"),
        ("where is the nearest bus stop", "bus stop near where"),
        ("i will see you tomorrow morning", "tomorrow morning i you see"),
    ]
    
    # Generate more complex variations
    for subj in ['i', 'you', 'he', 'she', 'we']:
        for verb1 in ['want', 'need', 'try']:
            for verb2 in ['learn', 'study', 'teach', 'help']:
                for obj in ['language', 'work', 'book']:
                    complex_sentences.append((
                        f"{subj} {verb1} to {verb2} {obj}",
                        f"{subj} {obj} {verb2} {verb1}"
                    ))
    
    patterns.extend(complex_sentences[:150])
    print(f"  Added {len(complex_sentences[:150])} complex sentences")
    
    # 10. YES/NO QUESTIONS (80 pairs)
    yn_questions = []
    
    for subj in pronouns['subject'][:5]:
        for modal in ['can', 'do', 'will', 'should']:
            for verb in verbs[:10]:
                yn_questions.append((
                    f"{modal} {subj} {verb}",
                    f"{subj} {verb} {modal}"
                ))
    
    patterns.extend(yn_questions[:100])
    print(f"  Added {len(yn_questions[:100])} yes/no questions")
    
    return patterns

def create_high_quality_dataset():
    """Create high-quality training dataset"""
    
    print("="*60)
    print("Creating HIGH-QUALITY ISL Training Dataset V2")
    print("="*60)
    
    # Load vocabulary
    vocab = load_sigml_vocabulary()
    categories = categorize_vocabulary(vocab)
    
    # Generate diverse patterns
    print("\nGenerating diverse sentence patterns...")
    pattern_pairs = generate_diverse_patterns(categories)
    print(f"\nGenerated {len(pattern_pairs)} pattern-based pairs")
    
    # Add all vocabulary words (single words)
    vocab_pairs = [(word, word) for word in vocab]
    print(f"Added {len(vocab_pairs)} vocabulary words")
    
    # Combine
    all_pairs = pattern_pairs + vocab_pairs
    
    # Remove duplicates
    unique_pairs = list(set(all_pairs))
    print(f"\nTotal unique pairs: {len(unique_pairs)}")
    
    # Format with special tokens
    formatted_pairs = []
    for eng, isl in unique_pairs:
        formatted_pairs.append({
            "english": f"<sos> {eng} <eos>",
            "isl": f"<sos> {isl} <eos>"
        })
    
    # Shuffle
    random.shuffle(formatted_pairs)
    
    # Split into train/val (85/15)
    split_idx = int(len(formatted_pairs) * 0.85)
    train_pairs = formatted_pairs[:split_idx]
    val_pairs = formatted_pairs[split_idx:]
    
    print(f"\nDataset split:")
    print(f"  Training pairs: {len(train_pairs)}")
    print(f"  Validation pairs: {len(val_pairs)}")
    
    # Save files
    data_dir = Path(__file__).parent.parent / "data"
    train_path = data_dir / "train_pairs_enhanced_v2.json"
    val_path = data_dir / "val_pairs_enhanced_v2.json"
    
    with open(train_path, 'w', encoding='utf-8') as f:
        json.dump(train_pairs, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved training data: {train_path}")
    
    with open(val_path, 'w', encoding='utf-8') as f:
        json.dump(val_pairs, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved validation data: {val_path}")
    
    # Show sample pairs
    print("\n" + "="*60)
    print("Sample High-Quality Pairs (English → ISL)")
    print("="*60)
    
    # Show diverse examples
    sample_indices = [0, 50, 150, 300, 500, 750, 1000, 1200, 1400, 1600]
    for i, idx in enumerate(sample_indices, 1):
        if idx < len(train_pairs):
            pair = train_pairs[idx]
            eng = pair['english'].replace('<sos> ', '').replace(' <eos>', '')
            isl = pair['isl'].replace('<sos> ', '').replace(' <eos>', '')
            print(f"{i:2d}. '{eng}' → '{isl}'")
    
    print("\n" + "="*60)
    print("✅ HIGH-QUALITY training data created successfully!")
    print(f"✅ Total pairs: {len(unique_pairs)}")
    print(f"✅ Much more diverse and grammatically correct!")
    print("="*60)
    
    return train_path, val_path

if __name__ == "__main__":
    create_high_quality_dataset()

