# Tool System Architecture

## Overview

This project implements a sophisticated, class-based tool management system with automatic discovery and registration. All tools follow a standardized structure and are automatically loaded when the application starts.

## Architecture Components

### 1. BaseTool (Abstract Base Class)

**Location**: `tools/base_tool.py`

**Purpose**: Enforces a standard structure for all tools.

**Required Methods**:
- `name` (property) - Unique tool identifier
- `description` (property) - LLM-readable description
- `execute` (method) - Tool's main logic

**Key Features**:
- Abstract base class using Python's ABC
- Automatic conversion to Strands-compatible format via `to_strands_tool()`
- Type hints enforced throughout

### 2. ToolRegistry (Auto-Discovery & Management)

**Location**: `tools/tool_manager.py`

**Purpose**: Manages tool lifecycle from discovery to registration.

**Key Features**:
- **Auto-discovery**: Scans `tools/` directory for tool classes
- **Validation**: Ensures tools inherit from BaseTool
- **Registration**: Instantiates and registers tools
- **Strands Conversion**: Converts to Strands-compatible format
- **Singleton Pattern**: Global `registry` instance

**Public Methods**:
```python
registry.auto_discover_tools()      # Discover all tools
registry.register(tool_instance)     # Manually register a tool
registry.get_tool(name)             # Get tool by name
registry.get_all_tools()            # Get all tools dict
registry.get_strands_tools()        # Get Strands-compatible tools
registry.list_tools()               # Print all tools
```

### 3. Individual Tools

**Location**: `tools/*.py` (one file per tool)

**Structure**:
```python
from .base_tool import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "tool_name"
    
    @property
    def description(self) -> str:
        return "Detailed description for LLM"
    
    def execute(self, *args, **kwargs):
        # Tool logic
        return result
```

## Workflow

### Startup Sequence

1. **Application starts** (`main.py`)
2. **Registry initializes** (imports `tool_manager.py`)
3. **Auto-discovery runs** (`registry.auto_discover_tools()`)
4. **Tools are discovered**:
   - Scans `tools/` directory
   - Finds Python files (excluding `_`, `base_tool.py`, `tool_manager.py`)
   - Imports each module
5. **Tools are validated**:
   - Checks inheritance from BaseTool
   - Verifies required methods exist
6. **Tools are registered**:
   - Instantiates each tool class
   - Converts to Strands format
   - Adds to registry
7. **Agent initializes** with `registry.get_strands_tools()`
8. **Ready to serve requests**

### Console Output

```
==================================================
INITIALIZING TOOL SYSTEM
==================================================
Discovering tools in: /path/to/backend/tools
✓ Registered tool: letter_counter
✓ Registered tool: word_counter

=== Registered Tools ===
  • letter_counter: Count the number of letters...
  • word_counter: Count the number of words...

Total: 2 tools

==================================================
```

## Benefits

### 1. Standardization
- All tools follow the same structure
- Enforced by abstract base class
- Type hints throughout
- Consistent error handling

### 2. Auto-Loading
- No manual registration needed
- Just create a file, restart server
- Tools are discovered automatically
- Hot-reloading ready

### 3. Validation
- Tools validated at startup
- Errors caught early
- Clear error messages
- No runtime surprises

### 4. Discoverability
- Easy to see all available tools
- `registry.list_tools()` shows everything
- Clear console output
- Well-documented

### 5. Testability
- Tools can be tested independently
- No dependencies on agent
- Pure Python classes
- Easy to mock

### 6. Maintainability
- Each tool is isolated
- Clear separation of concerns
- Easy to add/remove tools
- No coupling between tools

## Creating a New Tool

### Step 1: Create File
```bash
touch backend/tools/my_new_tool.py
```

### Step 2: Implement BaseTool
```python
from typing import Dict
from .base_tool import BaseTool

class MyNewTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_new_tool"
    
    @property
    def description(self) -> str:
        return """What this tool does.
        
        Args:
            param: Description
            
        Returns:
            Description of return value
        """
    
    def execute(self, param: str) -> Dict:
        # Your logic here
        return {
            "status": "success",
            "result": f"Processed: {param}"
        }
```

### Step 3: Restart Server
That's it! The tool will be automatically discovered and loaded.

## Integration with Strands

The `to_strands_tool()` method in BaseTool handles the conversion:

```python
def to_strands_tool(self):
    from strands import tool
    
    def tool_function(*args, **kwargs):
        return self.execute(*args, **kwargs)
    
    tool_function.__name__ = self.name
    tool_function.__doc__ = self.description
    
    return tool(tool_function)
```

This creates a Strands-compatible function with:
- Proper function name
- Proper docstring (for LLM understanding)
- `@tool` decorator applied

## Example Tools

### Letter Counter
- **File**: `tools/letter_counter.py`
- **Class**: `LetterCounterTool`
- **Purpose**: Count letters in text
- **Returns**: Total, breakdown, text length

### Word Counter
- **File**: `tools/word_counter.py`
- **Class**: `WordCounterTool`
- **Purpose**: Count and analyze words
- **Returns**: Count, avg length, longest/shortest word

## File Structure

```
backend/
├── main.py                 # Initializes registry and agent
└── tools/
    ├── __init__.py         # Package init
    ├── README.md          # Tool development guide
    ├── base_tool.py       # Abstract base class
    ├── tool_manager.py    # Registry and auto-discovery
    ├── letter_counter.py  # Letter counting tool
    ├── word_counter.py    # Word counting tool
    └── TOOL_SYSTEM.md    # This file
```

## Best Practices

1. **One tool per file**
2. **Clear, descriptive names**
3. **Detailed descriptions for LLM**
4. **Type hints everywhere**
5. **Return structured data (dicts)**
6. **Handle errors gracefully**
7. **Test tools independently**
8. **Document parameters and returns**

## Advanced Usage

### Manual Registration
```python
from tools.tool_manager import registry
from tools.my_tool import MyTool

tool = MyTool()
registry.register(tool)
```

### Getting Specific Tool
```python
from tools.tool_manager import registry

letter_tool = registry.get_tool("letter_counter")
result = letter_tool.execute("Hello World")
```

### Testing Tools
```python
from tools.letter_counter import LetterCounterTool

def test_letter_counter():
    tool = LetterCounterTool()
    result = tool.execute("Hello")
    assert result["total"] == 5
```

## Error Handling

The registry catches and reports errors during discovery:

```python
try:
    module = importlib.import_module(f'tools.{module_name}')
    # ... registration logic
except Exception as e:
    print(f"✗ Error loading tool from {filename}: {str(e)}")
```

This ensures:
- Application doesn't crash on tool errors
- Clear error messages
- Other tools still load successfully

## Future Enhancements

Possible improvements:
- Tool categories/tags
- Tool dependencies
- Tool versioning
- Hot-reloading without restart
- Tool configuration files
- Tool testing framework
- Tool metrics/analytics

