from __future__ import annotations


class AgentRuntimeError(Exception):
    """Base exception for deterministic Agent runtime failures."""


class AgentValidationError(AgentRuntimeError):
    """Raised when a run request cannot be accepted."""


class AgentWorkflowNotRegisteredError(AgentRuntimeError):
    """Raised when no workflow handler is registered for the requested workflow."""


class AgentSafetyBlockedError(AgentRuntimeError):
    """Raised when deterministic safety checks block execution."""
