"""
Tool Manager for automatic tool discovery and registration.
"""
import os
import importlib
import inspect
from typing import List, Dict, Type
from .base_tool import BaseTool


class ToolRegistry:
    """
    Registry for managing and auto-loading tools.
    
    This class:
    1. Discovers all tool classes in the tools directory
    2. Validates that they inherit from BaseTool
    3. Instantiates and registers them
    4. Converts them to Strands-compatible tools
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._strands_tools: List = []
    
    def register(self, tool_instance: BaseTool) -> None:
        """
        Register a tool instance.
        
        Args:
            tool_instance: An instance of a class that inherits from BaseTool
            
        Raises:
            TypeError: If tool_instance doesn't inherit from BaseTool
        """
        if not isinstance(tool_instance, BaseTool):
            raise TypeError(f"Tool must inherit from BaseTool, got {type(tool_instance)}")
        
        tool_name = tool_instance.name
        if tool_name in self._tools:
            print(f"Warning: Tool '{tool_name}' already registered. Replacing...")
        
        self._tools[tool_name] = tool_instance
        self._strands_tools.append(tool_instance.to_strands_tool())
        print(f"✓ Registered tool: {tool_name}")
    
    def auto_discover_tools(self, tools_directory: str = None) -> None:
        """
        Automatically discover and register all tools in the tools directory.
        
        Args:
            tools_directory: Path to the tools directory. If None, uses the current package.
        """
        if tools_directory is None:
            tools_directory = os.path.dirname(__file__)
        
        print(f"Discovering tools in: {tools_directory}")
        
        # Get all Python files in the tools directory
        for filename in os.listdir(tools_directory):
            if filename.endswith('.py') and not filename.startswith('_') and filename not in ['base_tool.py', 'tool_manager.py']:
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module = importlib.import_module(f'tools.{module_name}')
                    
                    # Find all classes in the module that inherit from BaseTool
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Check if it's a BaseTool subclass and not BaseTool itself
                        if issubclass(obj, BaseTool) and obj is not BaseTool:
                            # Instantiate and register the tool
                            tool_instance = obj()
                            self.register(tool_instance)
                            
                except Exception as e:
                    print(f"✗ Error loading tool from {filename}: {str(e)}")
    
    def get_tool(self, tool_name: str) -> BaseTool:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            The tool instance
            
        Raises:
            KeyError: If tool not found
        """
        return self._tools[tool_name]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_strands_tools(self) -> List:
        """
        Get all tools in Strands-compatible format.
        
        Returns:
            List of Strands-compatible tool functions
        """
        return self._strands_tools.copy()
    
    def list_tools(self) -> None:
        """Print all registered tools."""
        print("\n=== Registered Tools ===")
        for name, tool in self._tools.items():
            print(f"  • {name}: {tool.description}")
        print(f"\nTotal: {len(self._tools)} tools\n")
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __repr__(self) -> str:
        return f"ToolRegistry(tools={len(self._tools)})"


# Global registry instance
registry = ToolRegistry()

