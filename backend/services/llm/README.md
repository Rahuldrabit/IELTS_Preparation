# LLM Provider Module

This module provides a unified, modular interface for accessing different LLM providers. It replaces the previous global `GemmaClient` singleton with a configurable provider system.

## Quick Start

```python
# New code - use this pattern
from services.llm import get_llm_client, LLMClientError

try:
    client = get_llm_client()
    response = client.generate_text("Your prompt here")
except LLMClientError as e:
    # Handle error
    pass
```

## Provider Priority

Providers are tried in this order at startup:

1. **OpenRouter** (cloud) — if `OPENROUTER_API_KEY` is set
2. **Google AI SDK** (cloud) — if `GEMINI_API_KEY` is set
3. **LM Studio** (local) — fallback to local inference

## Configuration

### Environment Variables

```bash
# OpenRouter (recommended for production)
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=google/gemma-3-27b-it  # or any model from openrouter.ai

# Google AI SDK (alternative cloud option)
GEMINI_API_KEY=your-key-here
GEMMA_MODEL=gemma-4-27b-it

# LM Studio (local development)
LMSTUDIO_MODEL=local-model  # Model name loaded in LM Studio
LMSTUDIO_MAX_TOKENS=4096
```

## Usage Patterns

### Basic Text Generation

```python
from services.llm import get_llm_client

client = get_llm_client()
text = client.generate_text(
    prompt="Write a short greeting",
    system_prompt="You are a helpful assistant",
    temperature=0.7
)
```

### Structured Output (JSON)

```python
from pydantic import BaseModel
from services.llm import get_llm_client

class EssayScore(BaseModel):
    band: float
    feedback: str
    improvements: list[str]

client = get_llm_client()
result = client.generate_structured(
    prompt="Score this essay: ...",
    schema=EssayScore,
    temperature=0.0
)
print(result.band)  # Access as typed object
```

### Task-Specific Client (Future Feature)

```python
from services.llm import get_llm_client_for_task

# Future: This will route to the best model for each task type
client = get_llm_client_for_task("writing_scoring")
```

### Health Check

```python
from services.llm import get_llm_client

client = get_llm_client()
status = client.health_check()
print(status)  # {"provider": "openrouter", "model": "...", "status": "ok"}
```

## Backward Compatibility

Existing code using the old import continues to work:

```python
# This still works (deprecated but supported)
from services.ai_agent.gemma_client import get_gemma_client, GemmaClientError

client = get_gemma_client()  # Delegates to new provider system
```

However, new code should use:

```python
from services.llm import get_llm_client, LLMClientError
```

## Adding New Providers

1. Create a new provider in `services/llm/providers/`:

```python
# services/llm/providers/my_provider.py
from services.llm.provider import LLMClient, LLMClientError

class MyProvider(LLMClient):
    @property
    def provider_name(self) -> str:
        return "my_provider"
    
    @property
    def model_name(self) -> str:
        return "my-model"
    
    def generate_text(self, prompt, system_prompt=None, temperature=0.3):
        # Implement your provider logic
        pass
    
    # ... implement other required methods
```

2. Add to `services/llm/providers/__init__.py`

3. Add initialization logic in `services/llm/provider.py`

## Provider Capabilities

| Provider | Text | Structured | Audio | Images |
|----------|------|------------|-------|--------|
| OpenRouter | ✅ | ✅ | ❌ | ❌ |
| Google AI | ✅ | ✅ | ✅ | ✅ |
| LM Studio | ✅ | ✅ | ❌ | ❌ |

## Architecture

```
services/llm/
├── __init__.py           # Public API exports
├── provider.py           # Provider registry and get_llm_client()
└── providers/
    ├── __init__.py
    ├── openrouter.py     # OpenRouter implementation
    ├── google.py         # Google AI SDK implementation
    └── lmstudio.py       # LM Studio implementation
```
