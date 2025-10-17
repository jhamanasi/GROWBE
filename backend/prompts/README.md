# Prompts Directory

This directory contains system prompts for the AI agent, allowing for easy versioning, A/B testing, and environment-specific configurations.

## Architecture

The prompt system uses a dynamic loading approach where prompts are stored as text files and loaded at runtime. This provides several benefits:

- **Version Control**: Easy to track prompt changes
- **A/B Testing**: Switch between prompts without code changes
- **Environment-based**: Different prompts for dev/staging/prod
- **Backup**: Keep old prompts for rollback
- **Collaboration**: Team can work on prompts independently

## Usage

### Default Behavior
The system automatically loads the default prompt using this priority:
1. Environment variable `PROMPT_NAME`
2. `ottawa-v1.txt` (current default)
3. First available prompt file

### Loading Specific Prompts
```python
from utils.prompt_loader import load_system_prompt

# Load default prompt
prompt = load_system_prompt()

# Load specific prompt
prompt = load_system_prompt('ottawa-v2')
```

### Environment Variables
Set `PROMPT_NAME` environment variable to use a specific prompt:
```bash
export PROMPT_NAME=ottawa-v2
```

## Current Prompts

### ottawa-v1.txt
- **Purpose**: Ottawa-focused real estate agent
- **Features**: Canadian currency, metric measurements, Ottawa neighborhoods
- **Status**: Production default

## Adding New Prompts

1. Create a new `.txt` file in this directory
2. Use descriptive naming: `ottawa-v2.txt`, `general-v1.txt`, etc.
3. The system will automatically detect new prompts
4. Test with: `python utils/prompt_loader.py`

## Prompt Naming Convention

- `ottawa-v1.txt` - Ottawa-specific agent (version 1)
- `ottawa-v2.txt` - Updated Ottawa agent (version 2)
- `general-v1.txt` - Generic realtor agent
- `test-v1.txt` - Testing prompt

## Testing Prompts

```bash
# List available prompts
python utils/prompt_loader.py

# Test specific prompt
python -c "from utils.prompt_loader import load_system_prompt; print(load_system_prompt('ottawa-v1'))"
```

## Best Practices

1. **Version Control**: Always version your prompts
2. **Documentation**: Add comments in prompt files for clarity
3. **Testing**: Test prompts before deploying
4. **Backup**: Keep old versions for rollback
5. **Naming**: Use descriptive, consistent naming

## File Structure

```
prompts/
├── README.md              # This file
├── ottawa-v1.txt         # Current Ottawa agent prompt
├── ottawa-v2.txt         # Future Ottawa agent version
└── general-v1.txt        # Generic realtor prompt
```
