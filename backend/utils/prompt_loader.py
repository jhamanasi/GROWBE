"""
Prompt Loader Utility

This module provides utilities for loading and managing system prompts
from the prompts/ directory. This allows for easy prompt versioning,
A/B testing, and environment-specific configurations.
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    """Utility class for loading system prompts from the prompts directory."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Path to the prompts directory (relative to backend/)
        """
        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a system prompt from the prompts directory.
        
        Args:
            prompt_name: Name of the prompt file (e.g., "ottawa-v1", "general-v1")
                        Can include or exclude .txt extension
            
        Returns:
            The prompt content as a string
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            IOError: If there's an error reading the file
        """
        # Add .txt extension if not present
        if not prompt_name.endswith('.txt'):
            prompt_name += '.txt'
        
        prompt_path = self.prompts_dir / prompt_name
        
        if not prompt_path.exists():
            available_prompts = self.list_available_prompts()
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Available prompts: {', '.join(available_prompts)}"
            )
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                logger.info(f"Loaded prompt: {prompt_name}")
                return content
        except Exception as e:
            raise IOError(f"Error reading prompt file {prompt_path}: {e}")
    
    def list_available_prompts(self) -> list:
        """
        List all available prompt files in the prompts directory.
        
        Returns:
            List of prompt names (without .txt extension)
        """
        try:
            prompt_files = [f.stem for f in self.prompts_dir.glob("*.txt")]
            return sorted(prompt_files)
        except Exception as e:
            logger.error(f"Error listing prompts: {e}")
            return []
    
    def get_default_prompt(self) -> str:
        """
        Get the default prompt. Priority order:
        1. Environment variable PROMPT_NAME
        2. ottawa-v1 (current default)
        3. First available prompt
        
        Returns:
            The default prompt content
        """
        # Check environment variable first
        env_prompt = os.getenv('PROMPT_NAME')
        if env_prompt:
            try:
                return self.load_prompt(env_prompt)
            except FileNotFoundError:
                logger.warning(f"Environment prompt '{env_prompt}' not found, falling back to default")
        
        # Try ottawa-v1 as default
        try:
            return self.load_prompt('ottawa-v1')
        except FileNotFoundError:
            logger.warning("ottawa-v1 prompt not found, trying first available")
        
        # Fall back to first available prompt
        available = self.list_available_prompts()
        if available:
            return self.load_prompt(available[0])
        
        raise FileNotFoundError("No prompts available in the prompts directory")

# Convenience function for easy usage
def load_system_prompt(prompt_name: Optional[str] = None) -> str:
    """
    Load a system prompt. If no prompt_name is provided, uses the default.
    
    Args:
        prompt_name: Name of the prompt to load (optional)
        
    Returns:
        The prompt content as a string
    """
    loader = PromptLoader()
    
    if prompt_name:
        return loader.load_prompt(prompt_name)
    else:
        return loader.get_default_prompt()

# Example usage:
if __name__ == "__main__":
    # Test the prompt loader
    loader = PromptLoader()
    
    print("Available prompts:", loader.list_available_prompts())
    
    try:
        # Load default prompt
        default_prompt = loader.get_default_prompt()
        print(f"Default prompt loaded, length: {len(default_prompt)} characters")
        
        # Load specific prompt
        ottawa_prompt = loader.load_prompt('ottawa-v1')
        print(f"Ottawa prompt loaded, length: {len(ottawa_prompt)} characters")
        
    except Exception as e:
        print(f"Error: {e}")
