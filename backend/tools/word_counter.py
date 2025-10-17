"""
Word Counter Tool - Counts words in text.
"""
from typing import Dict
from .base_tool import BaseTool


class WordCounterTool(BaseTool):
    """
    A tool for counting words in text.
    
    This tool analyzes text and counts the number of words,
    providing detailed statistics.
    """
    
    @property
    def name(self) -> str:
        return "word_counter"
    
    @property
    def description(self) -> str:
        return """Count the number of words in the given text.
    
    This tool counts words in the text by splitting on whitespace.
    It also provides additional statistics like average word length.
    
    Args:
        text: The text to analyze
        
    Returns:
        A dictionary containing:
        - total_words: Total number of words
        - average_word_length: Average length of words
        - longest_word: The longest word in the text
        - shortest_word: The shortest word in the text
    """
    
    def execute(self, text: str) -> Dict:
        """
        Count words in the provided text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with word count statistics
        """
        # Split text into words
        words = text.split()
        
        if not words:
            return {
                "total_words": 0,
                "average_word_length": 0,
                "longest_word": "",
                "shortest_word": ""
            }
        
        # Calculate statistics
        word_lengths = [len(word) for word in words]
        average_length = sum(word_lengths) / len(word_lengths)
        
        longest_word = max(words, key=len)
        shortest_word = min(words, key=len)
        
        return {
            "total_words": len(words),
            "average_word_length": round(average_length, 2),
            "longest_word": longest_word,
            "shortest_word": shortest_word
        }

