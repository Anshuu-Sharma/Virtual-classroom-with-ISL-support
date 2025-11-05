"""
ISL Mapping Service
Maps English words to ISL glosses using sigmlFiles.json
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ISLMapper:
    """Maps English words to ISL glosses"""
    
    def __init__(self, sigml_json_path: str = None):
        """
        Initialize mapper with sigmlFiles.json
        
        Args:
            sigml_json_path: Path to sigmlFiles.json
        """
        if sigml_json_path is None:
            base_dir = Path(__file__).parent.parent
            sigml_json_path = base_dir / "js" / "sigmlFiles.json"
        
        self.sigml_json_path = Path(sigml_json_path)
        self.word_to_gloss: Dict[str, str] = {}
        self.gloss_to_word: Dict[str, str] = {}
        
        self._load_mappings()
    
    def _load_mappings(self):
        """Load word-to-gloss mappings from sigmlFiles.json"""
        try:
            if not self.sigml_json_path.exists():
                logger.warning(f"sigmlFiles.json not found at {self.sigml_json_path}")
                return
            
            with open(self.sigml_json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract JSON array (skip the "sigmlList = " part)
                start = content.find('[')
                end = content.rfind(']') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    sigml_list = json.loads(json_str)
                    
                    for item in sigml_list:
                        word = item.get('name', '').lower().strip()
                        if word and word not in ['', 'EOL']:
                            # Store word -> gloss mapping
                            # The gloss is the same as the word in this case
                            # But we can also derive from filename
                            filename = item.get('fileName', '')
                            if filename:
                                # Remove .sigml extension
                                gloss = filename.replace('.sigml', '').lower()
                                self.word_to_gloss[word] = gloss
                                self.gloss_to_word[gloss] = word
                    
                    logger.info(f"Loaded {len(self.word_to_gloss)} word-to-gloss mappings")
                else:
                    logger.error("Could not parse sigmlFiles.json")
                    
        except Exception as e:
            logger.error(f"Error loading sigmlFiles.json: {e}")
    
    def map_word_to_gloss(self, word: str) -> Optional[str]:
        """
        Map English word to ISL gloss
        
        Args:
            word: English word (lowercase, should already be lemmatized)
            
        Returns:
            ISL gloss name or None if not found
        """
        word = word.lower().strip()
        # Remove punctuation
        word = word.rstrip('.,!?;:')
        
        if not word:
            return None
        
        # Direct lookup (word should already be lemmatized)
        if word in self.word_to_gloss:
            return self.word_to_gloss[word]
        
        # Try removing common suffixes (in case lemmatization didn't work)
        base_forms = [
            word.rstrip('s'),  # plural -> singular
            word.rstrip('ing'),  # gerund -> base
            word.rstrip('ed'),  # past tense -> base
            word.rstrip('er'),  # comparative -> base
            word.rstrip('est'),  # superlative -> base
            word.rstrip('ly'),  # adverb -> base
            word.rstrip('tion'),  # action -> act
            word.rstrip('sion'),  # decision -> decide
        ]
        
        # Try base forms
        for base in set(base_forms):  # Use set to avoid duplicates
            if base and base != word and base in self.word_to_gloss:
                return self.word_to_gloss[base]
        
        # Try adding common suffixes (in case we have base form but need to find it)
        if word + 's' in self.word_to_gloss:
            return self.word_to_gloss[word + 's']
        if word + 'ing' in self.word_to_gloss:
            return self.word_to_gloss[word + 'ing']
        
        # Try partial matches (for compound words) - but be careful!
        # Only match if word is a complete word match, not substring
        # e.g., "students" should match "student", not "d" or "s"
        words_in_gloss = []
        for w in self.word_to_gloss.keys():
            # Check if word starts with w (word is a variation) or w starts with word (word is base)
            if word.startswith(w) and len(w) >= 3:  # Only if base is at least 3 chars
                words_in_gloss.append(w)
            elif w.startswith(word) and len(word) >= 3:  # Or if word is base
                words_in_gloss.append(w)
        
        if words_in_gloss:
            # Return the longest match (most specific)
            best_match = max(words_in_gloss, key=len)
            return self.word_to_gloss[best_match]
        
        # If not found, return None (will be handled as letter-by-letter)
        return None
    
    def map_tokens_to_isl(self, tokens: List[str]) -> List[str]:
        """
        Map list of English tokens to ISL glosses
        
        Args:
            tokens: List of English words/tokens
            
        Returns:
            List of ISL glosses (or original token if not found)
        """
        isl_glosses = []
        
        for token in tokens:
            token = token.lower().strip()
            if not token:
                continue
            
            # Try to map to ISL gloss
            gloss = self.map_word_to_gloss(token)
            if gloss:
                isl_glosses.append(gloss)
            else:
                # Not found in mapping - keep original (will be handled as letters)
                isl_glosses.append(token)
        
        return isl_glosses


# Global instance
_isl_mapper = None

def get_isl_mapper() -> ISLMapper:
    """Get or create ISL mapper instance"""
    global _isl_mapper
    if _isl_mapper is None:
        _isl_mapper = ISLMapper()
    return _isl_mapper

