from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.agent.schemas import AgentToolMetadata


class AgentTool(ABC):
    metadata: AgentToolMetadata

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload

    @abstractmethod
    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute is only an interface in Phase 07.B; real tools come later."""
