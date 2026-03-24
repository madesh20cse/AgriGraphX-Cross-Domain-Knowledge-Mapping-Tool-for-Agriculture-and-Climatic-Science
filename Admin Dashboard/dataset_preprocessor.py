"""
dataset_preprocessor.py — Dataset Preprocessing Module

Implements preprocessing tasks for uploaded datasets:
- Remove special characters
- Normalize text
- Convert to lowercase
- Prepare for entity and relation extraction

This module prepares datasets for later NLP processing in Module 2+.
"""

import re
import unicodedata
from typing import Tuple, Dict, List
from datetime import datetime


class DatasetPreprocessor:
    """Handles preprocessing of datasets for entity/relation extraction."""
    
    def __init__(self):
        """Initialize preprocessor with stopwords and patterns."""
        self.common_stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
    
    def remove_special_characters(self, text: str) -> str:
        """
        Remove special characters while preserving structure.
        Keep: letters, numbers, spaces, periods, commas, hyphens.
        
        Args:
            text: Input text
            
        Returns:
            Text with special characters removed
        """
        # Keep alphanumeric, spaces, basic punctuation
        text = re.sub(r'[^\w\s\.\-,:\(\)\/]', '', text)
        return text
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text using NFKD unicode normalization.
        Removes accents and special unicode characters.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # NFKD decomposition
        text = unicodedata.normalize('NFKD', text)
        # Remove combining characters (accents)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        return text
    
    def lowercase(self, text: str) -> str:
        """
        Convert text to lowercase.
        
        Args:
            text: Input text
            
        Returns:
            Lowercase text
        """
        return text.lower()
    
    def clean_whitespace(self, text: str) -> str:
        """
        Clean excessive whitespace.
        
        Args:
            text: Input text
            
        Returns:
            Text with cleaned whitespace
        """
        # Process line by line so we preserve logical line breaks for previews
        # and downstream sentence/record-based processing.
        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            # Strip leading/trailing spaces and collapse internal spaces/tabs
            stripped = line.strip()
            stripped = re.sub(r"[ \t]+", " ", stripped)
            cleaned_lines.append(stripped)

        return "\n".join(cleaned_lines).strip("\n")
    
    def remove_urls(self, text: str) -> str:
        """
        Remove URLs from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without URLs
        """
        url_pattern = r'https?://\S+|www\.\S+'
        return re.sub(url_pattern, '', text)
    
    def remove_emails(self, text: str) -> str:
        """
        Remove email addresses from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without emails
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, '', text)
    
    def remove_numbers(self, text: str, keep_numbers: bool = True) -> str:
        """
        Optionally remove numbers.
        
        Args:
            text: Input text
            keep_numbers: If False, remove all numbers
            
        Returns:
            Text with/without numbers
        """
        if not keep_numbers:
            return re.sub(r'\d+', '', text)
        return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Split on periods, exclamation marks, question marks
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def extract_paragraphs(self, text: str) -> List[str]:
        """
        Extract paragraphs from text.
        
        Args:
            text: Input text
            
        Returns:
            List of paragraphs
        """
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs
    
    def preprocess_full(self, text: str, lowercase: bool = True, 
                       remove_urls: bool = True, remove_emails: bool = True,
                       remove_special: bool = True, normalize: bool = True) -> str:
        """
        Apply full preprocessing pipeline.
        
        Args:
            text: Input text
            lowercase: Convert to lowercase
            remove_urls: Remove URLs
            remove_emails: Remove emails
            remove_special: Remove special characters
            normalize: Normalize unicode
            
        Returns:
            Preprocessed text
        """
        # Sequential preprocessing
        if remove_urls:
            text = self.remove_urls(text)
        
        if remove_emails:
            text = self.remove_emails(text)
        
        if normalize:
            text = self.normalize_text(text)
        
        if remove_special:
            text = self.remove_special_characters(text)
        
        if lowercase:
            text = self.lowercase(text)
        
        text = self.clean_whitespace(text)
        
        return text
    
    def generate_report(self, original_text: str, processed_text: str) -> Dict:
        """
        Generate preprocessing report with statistics.
        
        Args:
            original_text: Original text
            processed_text: Processed text
            
        Returns:
            Dictionary with preprocessing statistics
        """
        original_chars = len(original_text)
        processed_chars = len(processed_text)
        
        original_words = len(original_text.split())
        processed_words = len(processed_text.split())
        
        original_sentences = len(self.extract_sentences(original_text))
        processed_sentences = len(self.extract_sentences(processed_text))
        
        return {
            "original_characters": original_chars,
            "processed_characters": processed_chars,
            "characters_removed": original_chars - processed_chars,
            "percentage_reduction": f"{((original_chars - processed_chars) / original_chars * 100):.2f}%" if original_chars > 0 else "0%",
            "original_words": original_words,
            "processed_words": processed_words,
            "words_removed": original_words - processed_words,
            "original_sentences": original_sentences,
            "processed_sentences": processed_sentences,
            "timestamp": datetime.now().isoformat()
        }


# Dataset categorization by domain
DATASET_CATEGORIES = {
    "agriculture": {
        "name": "Agriculture",
        "emoji": "🌾",
        "description": "Agricultural research, farming techniques, crop data",
        "keywords": ["agriculture", "crop", "farm", "farming", "soil", "irrigation", "pesticide", "fertilizer", "yield", "harvest"]
    },
    "climate": {
        "name": "Climate",
        "emoji": "🌍",
        "description": "Climate data, weather reports, environmental studies",
        "keywords": ["climate", "weather", "temperature", "precipitation", "greenhouse", "carbon", "emission", "warming", "sea level", "drought"]
    },
    "data_science": {
        "name": "Data Science",
        "emoji": "📊",
        "description": "Data analysis, statistics, machine learning datasets",
        "keywords": ["data", "analysis", "statistics", "machine learning", "prediction", "model", "dataset", "analytics", "algorithm", "science"]
    },
    "general": {
        "name": "General Knowledge",
        "emoji": "📚",
        "description": "General knowledge articles and documents",
        "keywords": []
    }
}


def categorize_dataset(filename: str, content_preview: str) -> str:
    """
    Categorize dataset by filename and content preview.
    
    Args:
        filename: Dataset filename
        content_preview: First 500 chars of content
        
    Returns:
        Category name (agriculture, climate, data_science, general)
    """
    # Combine filename and content for analysis
    analysis_text = (filename + " " + content_preview).lower()
    
    # Check each category
    for category, info in DATASET_CATEGORIES.items():
        if category == "general":
            continue
        
        # Count keyword matches
        matches = sum(1 for keyword in info["keywords"] if keyword in analysis_text)
        if matches >= 2:  # At least 2 keyword matches
            return category
    
    return "general"


def get_category_info(category: str) -> Dict:
    """
    Get information about a dataset category.
    
    Args:
        category: Category name
        
    Returns:
        Dictionary with category information
    """
    return DATASET_CATEGORIES.get(category, DATASET_CATEGORIES["general"])
