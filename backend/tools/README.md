# Tools Directory

This directory contains all custom tools for the AI agent. Tools are automatically discovered and loaded when the application starts.

## Architecture

### Tool System Components

1. **BaseTool** (`base_tool.py`) - Abstract base class that all tools must inherit from
2. **ToolRegistry** (`tool_manager.py`) - Manages tool discovery, registration, and conversion to Strands format
3. **Individual Tools** - Each tool in its own file, implementing the BaseTool interface

## Creating a New Tool

### Step 1: Create a New File

Create a new Python file in this directory (e.g., `my_tool.py`)

### Step 2: Implement the BaseTool Interface

```python
from typing import Dict, Any
from .base_tool import BaseTool


class MyCustomTool(BaseTool):
    """
    Description of what your tool does.
    """
    
    @property
    def name(self) -> str:
        """Return the tool name (lowercase, underscores)."""
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        """
        Return a detailed description.
        This is what the LLM uses to understand when to use this tool.
        """
        return """What this tool does and how to use it.
        
        Args:
            param1: Description of first parameter
            param2: Description of second parameter
            
        Returns:
            Description of what the tool returns
        """
    
    def execute(self, param1: str, param2: int) -> Dict[str, Any]:
        """
        Execute the tool's main functionality.
        
        Args:
            param1: First parameter
            param2: Second parameter
            
        Returns:
            Result of the tool execution
        """
        # Your tool logic here
        result = f"Processed {param1} with {param2}"
        
        return {
            "status": "success",
            "result": result
        }
```

### Step 3: That's It!

The tool will be automatically discovered and registered when the application starts. No need to manually register it anywhere.

## Tool Guidelines

### Required Methods

All tools **must** implement:
- `name` property - Returns the tool's unique identifier
- `description` property - Returns a detailed description for the LLM
- `execute` method - Contains the tool's logic

### Best Practices

1. **Clear Naming**: Use descriptive, lowercase names with underscores
2. **Detailed Descriptions**: The LLM relies on descriptions to know when to use the tool
3. **Type Hints**: Always use type hints for parameters and return values
4. **Docstrings**: Document your execute method thoroughly
5. **Error Handling**: Handle errors gracefully and return meaningful error messages
6. **Return Dictionaries**: Prefer returning dictionaries for structured data

### Example Return Format

```python
return {
    "status": "success",
    "data": result,
    "metadata": {
        "processing_time": 0.5,
        "items_processed": 10
    }
}
```

## Available Tools

### LetterCounterTool (`letter_counter.py`)
Counts letters in text, excluding spaces and special characters.

**Example usage:**
```
User: "How many letters are in 'Hello World'?"
Agent: *Uses letter_counter tool*
```

### WordCounterTool (`word_counter.py`)
Counts words in text and provides statistics like average word length.

**Example usage:**
```
User: "Count the words in this sentence"
Agent: *Uses word_counter tool*
```

## Tool Registry

The `ToolRegistry` class manages all tools:

- **Auto-discovery**: Scans the tools directory for tool classes
- **Validation**: Ensures tools inherit from BaseTool
- **Registration**: Instantiates and registers tools
- **Strands Conversion**: Converts tools to Strands-compatible format

### Registry API

```python
from tools.tool_manager import registry

# Get all tools
all_tools = registry.get_all_tools()

# Get a specific tool
letter_tool = registry.get_tool("letter_counter")

# Get Strands-compatible tools
strands_tools = registry.get_strands_tools()

# List all registered tools
registry.list_tools()
```

## Debugging Tools

When the application starts, you'll see:

```
==================================================
INITIALIZING TOOL SYSTEM
==================================================
Discovering tools in: /path/to/tools
✓ Registered tool: letter_counter
✓ Registered tool: word_counter

=== Registered Tools ===
  • letter_counter: Count the number of letters...
  • word_counter: Count the number of words...

Total: 2 tools
==================================================
```

## Advanced: Testing Tools

You can test tools individually:

```python
from tools.letter_counter import LetterCounterTool

tool = LetterCounterTool()
result = tool.execute("Hello World")
print(result)
# Output: {'total': 10, 'breakdown': {...}, ...}
```

## Files to Ignore

The auto-discovery system ignores:
- Files starting with `_` (like `__init__.py`)
- `base_tool.py` (the base class)
- `tool_manager.py` (the registry)
- Any non-Python files

## Architecture Benefits

1. **Standardization**: All tools follow the same structure
2. **Auto-loading**: No manual registration needed
3. **Validation**: Tools are validated at startup
4. **Discoverability**: Easy to see all available tools
5. **Testability**: Tools can be tested independently
6. **Maintainability**: Each tool is isolated in its own file

