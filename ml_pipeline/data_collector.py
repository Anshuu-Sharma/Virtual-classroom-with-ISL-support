"""
Data Collection Module
Collects user audio/text pairs, feedback, and annotations for training
"""

import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class DataCollector:
    """Collect and manage training data"""
    
    def __init__(self, db_path: str = "data/training_data.db"):
        """
        Initialize data collector
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Audio samples table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file_path TEXT NOT NULL,
                transcript TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                duration REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                metadata TEXT
            )
        ''')
        
        # Translation pairs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_text TEXT NOT NULL,
                isl_text TEXT NOT NULL,
                isl_gloss TEXT,
                sigml_file TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                metadata TEXT
            )
        ''')
        
        # User feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                translation_pair_id INTEGER,
                feedback_type TEXT,
                is_correct BOOLEAN,
                corrected_text TEXT,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (translation_pair_id) REFERENCES translation_pairs(id)
            )
        ''')
        
        # Annotations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_sample_id INTEGER,
                translation_pair_id INTEGER,
                annotation_type TEXT,
                annotation_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (audio_sample_id) REFERENCES audio_samples(id),
                FOREIGN KEY (translation_pair_id) REFERENCES translation_pairs(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def add_audio_sample(self, audio_file_path: str, transcript: str, 
                        language: str = "en", duration: Optional[float] = None,
                        user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """
        Add audio sample to database
        
        Returns:
            Sample ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
            INSERT INTO audio_samples 
            (audio_file_path, transcript, language, duration, user_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (audio_file_path, transcript, language, duration, user_id, metadata_json))
        
        sample_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added audio sample {sample_id}: {audio_file_path}")
        return sample_id
    
    def add_translation_pair(self, english_text: str, isl_text: str,
                           isl_gloss: Optional[str] = None,
                           sigml_file: Optional[str] = None,
                           source: str = "manual",
                           verified: bool = False,
                           metadata: Optional[Dict] = None) -> int:
        """
        Add English-ISL translation pair
        
        Returns:
            Pair ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
            INSERT INTO translation_pairs
            (english_text, isl_text, isl_gloss, sigml_file, source, verified, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (english_text, isl_text, isl_gloss, sigml_file, source, 
              int(verified), metadata_json))
        
        pair_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added translation pair {pair_id}: {english_text[:50]}...")
        return pair_id
    
    def add_feedback(self, translation_pair_id: int, feedback_type: str,
                    is_correct: bool, corrected_text: Optional[str] = None,
                    comments: Optional[str] = None) -> int:
        """
        Add user feedback on translation
        
        Returns:
            Feedback ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback
            (translation_pair_id, feedback_type, is_correct, corrected_text, comments)
            VALUES (?, ?, ?, ?, ?)
        ''', (translation_pair_id, feedback_type, int(is_correct), 
              corrected_text, comments))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added feedback {feedback_id} for pair {translation_pair_id}")
        return feedback_id
    
    def get_translation_pairs(self, verified_only: bool = False,
                             limit: Optional[int] = None) -> List[Tuple]:
        """
        Get translation pairs from database
        
        Returns:
            List of (id, english_text, isl_text, isl_gloss, sigml_file) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, english_text, isl_text, isl_gloss, sigml_file
            FROM translation_pairs
        '''
        
        if verified_only:
            query += ' WHERE verified = 1'
        
        query += ' ORDER BY created_at DESC'
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def export_to_json(self, output_path: str, verified_only: bool = True):
        """Export translation pairs to JSON file"""
        pairs = self.get_translation_pairs(verified_only=verified_only)
        
        data = []
        for pair_id, eng, isl, gloss, sigml in pairs:
            data.append({
                'id': pair_id,
                'english': eng,
                'isl': isl,
                'isl_gloss': gloss,
                'sigml_file': sigml
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(data)} pairs to {output_path}")

