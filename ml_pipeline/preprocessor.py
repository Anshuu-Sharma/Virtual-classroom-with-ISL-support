"""
Data Preprocessing Module
Preprocesses text and audio data for model training
"""

import re
import string
import logging
from typing import List, Tuple, Dict
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class TextPreprocessor:
    """Text preprocessing utilities"""
    
    def __init__(self, language: str = "english"):
        self.language = language
        self.lemmatizer = WordNetLemmatizer()
        try:
            self.stop_words = set(stopwords.words(language))
        except:
            self.stop_words = set(['a', 'an', 'the', 'is', 'are', 'was', 'were'])
    
    def clean_text(self, text: str, lower: bool = True, 
                   remove_punct: bool = False,
                   remove_stopwords: bool = False) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Input text
            lower: Convert to lowercase
            remove_punct: Remove punctuation
            remove_stopwords: Remove stop words
            
        Returns:
            Cleaned text
        """
        if lower:
            text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if remove_punct:
            text = text.translate(str.maketrans('', '', string.punctuation))
        
        if remove_stopwords:
            words = text.split()
            words = [w for w in words if w not in self.stop_words]
            text = ' '.join(words)
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        try:
            return word_tokenize(text)
        except:
            return text.split()
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens"""
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def preprocess_for_translation(self, text: str) -> str:
        """
        Preprocess text for translation model
        
        Args:
            text: Input English text
            
        Returns:
            Preprocessed text
        """
        # Clean text
        text = self.clean_text(text, lower=True, remove_punct=False)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Add sentence markers
        text = f"<sos> {text} <eos>"
        
        return text


class ISLPreprocessor:
    """ISL text preprocessing utilities"""
    
    def __init__(self):
        pass
    
    def preprocess_isl(self, isl_text: str) -> str:
        """
        Preprocess ISL text/gloss
        
        Args:
            isl_text: ISL text or gloss sequence
            
        Returns:
            Preprocessed ISL text
        """
        # Normalize whitespace
        isl_text = re.sub(r'\s+', ' ', isl_text).strip()
        
        # Add sentence markers
        isl_text = f"<sos> {isl_text} <eos>"
        
        return isl_text
    
    def extract_gloss_from_sigml(self, sigml_file_path: str) -> str:
        """
        Extract gloss from SiGML file
        
        Args:
            sigml_file_path: Path to SiGML file
            
        Returns:
            Gloss string
        """
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(sigml_file_path)
            root = tree.getroot()
            
            # Find gloss attribute
            for sign in root.iter():
                if 'gloss' in sign.attrib:
                    return sign.attrib['gloss']
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting gloss from {sigml_file_path}: {e}")
            return ""


class DataPreprocessor:
    """Main data preprocessing class"""
    
    def __init__(self):
        self.text_preprocessor = TextPreprocessor()
        self.isl_preprocessor = ISLPreprocessor()
    
    def preprocess_pair(self, english_text: str, isl_text: str) -> Tuple[str, str]:
        """
        Preprocess English-ISL translation pair
        
        Returns:
            Tuple of (preprocessed_english, preprocessed_isl)
        """
        preprocessed_eng = self.text_preprocessor.preprocess_for_translation(english_text)
        preprocessed_isl = self.isl_preprocessor.preprocess_isl(isl_text)
        
        return preprocessed_eng, preprocessed_isl
    
    def create_vocabulary(self, texts: List[str], min_freq: int = 2) -> Dict[str, int]:
        """
        Create vocabulary from texts
        
        Args:
            texts: List of texts
            min_freq: Minimum frequency for word to be included
            
        Returns:
            Dictionary mapping word to index
        """
        word_counts = {}
        
        for text in texts:
            tokens = self.text_preprocessor.tokenize(text.lower())
            for token in tokens:
                word_counts[token] = word_counts.get(token, 0) + 1
        
        # Filter by min frequency
        vocab = {'<pad>': 0, '<unk>': 1, '<sos>': 2, '<eos>': 3}
        
        idx = len(vocab)
        for word, count in sorted(word_counts.items()):
            if count >= min_freq:
                vocab[word] = idx
                idx += 1
        
        logger.info(f"Created vocabulary with {len(vocab)} words")
        return vocab

