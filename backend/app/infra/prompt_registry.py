"""Versioned prompt registry for LLMOps."""
from dataclasses import dataclass
from typing import Any
import hashlib
import json

@dataclass
class PromptVersion:
    name: str
    version: str
    template: str
    variables: list[str]
    metadata: dict[str, Any]

class PromptRegistry:
    def __init__(self):
        self._prompts: dict[str, list[PromptVersion]] = {}
    
    def register(self, prompt: PromptVersion):
        if prompt.name not in self._prompts:
            self._prompts[prompt.name] = []
        self._prompts[prompt.name].append(prompt)
    
    def get(self, name: str, version: str | None = None) -> PromptVersion:
        versions = self._prompts.get(name, [])
        if not versions:
            raise KeyError(f"Prompt {name} not found")
        if version:
            for v in versions:
                if v.version == version:
                    return v
            raise KeyError(f"Version {version} of prompt {name} not found")
        return versions[-1]  # Return latest
    
    def list_versions(self, name: str) -> list[str]:
        return [v.version for v in self._prompts.get(name, [])]

# Global registry
_registry = PromptRegistry()

def get_registry() -> PromptRegistry:
    return _registry
