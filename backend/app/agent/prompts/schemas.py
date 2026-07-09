from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class PromptRegistryError(Exception):
    """Base error for prompt registry failures."""


class PromptNotFoundError(PromptRegistryError):
    """Raised when a prompt name/version is not registered."""


class PromptRenderError(PromptRegistryError):
    """Raised when a prompt cannot be rendered with explicit variables."""


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    safety_notes: tuple[str, ...]
    allowed_intents: tuple[str, ...]
    created_at: str
    template: str

    @property
    def prompt_id(self) -> str:
        return f"{self.name}:{self.version}"

    def render(self, variables: dict[str, Any]) -> str:
        missing = [
            key
            for key, schema in self.input_schema.items()
            if schema.get("required", False) and key not in variables
        ]
        if missing:
            raise PromptRenderError(f"Missing required prompt variables: {', '.join(missing)}")
        rendered = self.template
        for key in self.input_schema:
            placeholder = "{{ " + key + " }}"
            if placeholder not in rendered:
                continue
            value = variables.get(key, "")
            rendered = rendered.replace(placeholder, _stringify(value))
        return rendered


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {item}" for key, item in value.items())
    return str(value)
