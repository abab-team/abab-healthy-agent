from __future__ import annotations


class AgentRuntimeError(Exception):
    """Base exception for deterministic Agent runtime failures."""


class AgentValidationError(AgentRuntimeError):
    """Raised when a run request cannot be accepted."""


class AgentWorkflowNotRegisteredError(AgentRuntimeError):
    """Raised when no workflow handler is registered for the requested workflow."""


class AgentSafetyBlockedError(AgentRuntimeError):
    """Raised when deterministic safety checks block execution."""


class AgentToolError(AgentRuntimeError):
    """Base exception for Agent tool registry failures."""


class AgentToolNotFoundError(AgentToolError):
    """Raised when a requested Agent tool is not registered."""


class AgentToolAlreadyRegisteredError(AgentToolError):
    """Raised when a tool name is registered more than once."""


class AgentToolDisabledError(AgentToolError):
    """Raised when a disabled tool is requested for execution."""


class AgentToolMetadataError(AgentToolError):
    """Raised when tool metadata is incomplete or unsafe."""


class AgentToolPermissionDeclarationError(AgentToolMetadataError):
    """Raised when tool metadata omits required permission declarations."""
