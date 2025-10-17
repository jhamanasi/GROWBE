"""
Letter Counter Tool - Counts letters in text.
"""
from typing import Dict
from .base_tool import BaseTool


class LetterCounterTool(BaseTool):
    """
    A tool for counting letters in text.
    
    This tool analyzes text and counts the number of letters,
    excluding spaces, numbers, and special characters.
    """
    
    @property
    def name(self) -> str:
        return "letter_counter"
    
    @property
    def description(self) -> str:
        return """Count the number of letters in the given text.
    
    This tool counts individual letters (a-z, A-Z) in the text,
    excluding spaces, numbers, and special characters.
    Returns a dictionary with the total count and breakdown by letter.
    
    Args:
        text: The text to analyze
        
    Returns:
        A dictionary containing:
        - total: Total number of letters
        - breakdown: Dictionary of each letter and its count
        - text_length: Total length of the input text
    """
    
    def execute(self, text: str) -> Dict:
        """
        Count letters in the provided text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with letter count statistics
        """
        # Count only letters (a-z, A-Z)
        letters = [char.lower() for char in text if char.isalpha()]
        total = len(letters)
        
        # Create breakdown by letter
        breakdown = {}
        for letter in letters:
            breakdown[letter] = breakdown.get(letter, 0) + 1
        
        # Sort breakdown alphabetically
        breakdown = dict(sorted(breakdown.items()))
        
        return {
            "total": total,
            "breakdown": breakdown,
            "text_length": len(text),
            "unique_letters": len(breakdown)
        }

