from __future__ import annotations


class AgentApiError(Exception):
    """Base exception for the minimal Agent API module."""


class AgentWorkflowNotAllowedError(AgentApiError):
    """Raised when the API request asks for a workflow that is not public yet."""

