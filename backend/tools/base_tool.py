"""
Base tool class for creating custom tools.
All custom tools should inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    All tools must implement:
    - name: str property
    - description: str property
    - execute: method that performs the tool's action
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Return a description of the tool.
        This description is used by the LLM to understand when to use the tool.
        """
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the tool's main functionality.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            The result of the tool execution
        """
        pass
    
    def to_strands_tool(self):
        """
        Convert this tool to a Strands-compatible tool function.
        
        Returns:
            A function decorated with @tool that can be used by Strands Agent
        """
        from strands import tool
        import functools
        import inspect
        
        # Create a wrapper function that preserves the original signature
        @functools.wraps(self.execute)
        def tool_function(*args, **kwargs):
            return self.execute(*args, **kwargs)
        
        # Explicitly set the signature to match the execute method
        tool_function.__signature__ = inspect.signature(self.execute)
        
        # Set the function name and docstring for Strands
        tool_function.__name__ = self.name
        tool_function.__doc__ = self.description
        
        # Apply the @tool decorator
        return tool(tool_function)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

