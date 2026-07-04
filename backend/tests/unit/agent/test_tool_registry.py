from __future__ import annotations

import sys
import unittest
from typing import Any

from app.agent.exceptions import (
    AgentToolAlreadyRegisteredError,
    AgentToolDisabledError,
    AgentToolMetadataError,
    AgentToolNotFoundError,
    AgentToolPermissionDeclarationError,
)
from app.agent.schemas import AgentToolMetadata
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools.base import AgentTool


class AgentToolRegistryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = AgentToolRegistry()

    def test_register_valid_fake_read_tool(self) -> None:
        tool = FakeTool()

        self.registry.register(tool)

        self.assertIs(self.registry.get_tool("fake.read_profile"), tool)

    def test_get_tool(self) -> None:
        tool = self.registry.register(FakeTool(name="fake.get"))

        self.assertIs(self.registry.get_tool("fake.get"), tool)

    def test_list_tools(self) -> None:
        first = self.registry.register(FakeTool(name="fake.one"))
        second = self.registry.register(FakeTool(name="fake.two"))

        self.assertEqual(self.registry.list_tools(), [first, second])

    def test_list_enabled_tools(self) -> None:
        enabled = self.registry.register(FakeTool(name="fake.enabled"))
        self.registry.register(FakeTool(name="fake.disabled", enabled=False))

        self.assertEqual(self.registry.list_enabled_tools(), [enabled])

    def test_filter_by_category(self) -> None:
        profile = self.registry.register(FakeTool(name="fake.profile", category="health_profile"))
        self.registry.register(FakeTool(name="fake.alert", category="alert"))

        self.assertEqual(self.registry.list_tools_by_category("health_profile"), [profile])

    def test_filter_by_access_mode(self) -> None:
        read = self.registry.register(FakeTool(name="fake.read", access_mode="read"))
        self.registry.register(
            FakeTool(
                name="fake.write",
                access_mode="write",
                risk_level="high",
                requires_confirmation=True,
            )
        )

        self.assertEqual(self.registry.list_tools_by_access_mode("read"), [read])

    def test_filter_by_risk_level(self) -> None:
        low = self.registry.register(FakeTool(name="fake.low", risk_level="low"))
        self.registry.register(FakeTool(name="fake.medium", risk_level="medium"))

        self.assertEqual(self.registry.list_tools_by_risk_level("low"), [low])

    def test_duplicate_name_raises(self) -> None:
        self.registry.register(FakeTool())

        with self.assertRaises(AgentToolAlreadyRegisteredError):
            self.registry.register(FakeTool())

    def test_missing_tool_raises(self) -> None:
        with self.assertRaises(AgentToolNotFoundError):
            self.registry.get_tool("fake.missing")

    def test_disabled_tool_is_not_allowed(self) -> None:
        self.registry.register(FakeTool(enabled=False))

        with self.assertRaises(AgentToolDisabledError):
            self.registry.ensure_tool_allowed("fake.read_profile")

    def test_write_tool_requires_permission(self) -> None:
        with self.assertRaises(AgentToolPermissionDeclarationError):
            self.registry.register(
                FakeTool(
                    access_mode="write",
                    risk_level="high",
                    requires_confirmation=True,
                    required_permission_type=None,
                    required_permission_action=None,
                )
            )

    def test_draft_tool_requires_permission(self) -> None:
        with self.assertRaises(AgentToolPermissionDeclarationError):
            self.registry.register(
                FakeTool(
                    access_mode="draft",
                    required_permission_type=None,
                    required_permission_action=None,
                )
            )

    def test_high_risk_tool_requires_confirmation(self) -> None:
        with self.assertRaises(AgentToolMetadataError):
            self.registry.register(FakeTool(risk_level="high", requires_confirmation=False))

    def test_critical_risk_tool_requires_confirmation(self) -> None:
        with self.assertRaises(AgentToolMetadataError):
            self.registry.register(FakeTool(risk_level="critical", requires_confirmation=False))

    def test_system_low_risk_tool_can_omit_business_permission(self) -> None:
        tool = self.registry.register(
            FakeTool(
                category="system",
                required_permission_type=None,
                required_permission_action=None,
            )
        )

        self.assertIs(self.registry.ensure_tool_allowed("fake.read_profile"), tool)

    def test_system_none_access_tool_can_omit_business_permission(self) -> None:
        tool = self.registry.register(
            FakeTool(
                category="system",
                access_mode="none",
                required_permission_type=None,
                required_permission_action=None,
            )
        )

        self.assertEqual(self.registry.list_tools_by_access_mode("none"), [tool])

    def test_registry_does_not_import_llm(self) -> None:
        sys.modules.pop("app.agent.llm_client", None)

        self.registry.register(FakeTool())

        self.assertNotIn("app.agent.llm_client", sys.modules)

    def test_registry_does_not_import_db(self) -> None:
        sys.modules.pop("app.db.session", None)

        self.registry.register(FakeTool())

        self.assertNotIn("app.db.session", sys.modules)

    def test_registry_does_not_create_agent_tool_calls(self) -> None:
        sys.modules.pop("app.agent.models", None)

        self.registry.register(FakeTool())

        self.assertNotIn("app.agent.models", sys.modules)

    def test_register_does_not_execute_fake_tool_or_read_health_data(self) -> None:
        tool = FakeTool()

        self.registry.register(tool)

        self.assertFalse(tool.executed)
        self.assertFalse(tool.health_data_read)

    def test_invalid_metadata_is_rejected(self) -> None:
        with self.assertRaises(AgentToolMetadataError):
            self.registry.register(FakeTool(category="health_profile", risk_level="unknown"))


class FakeTool(AgentTool):
    def __init__(
        self,
        *,
        name: str = "fake.read_profile",
        category: str = "health_profile",
        access_mode: str = "read",
        risk_level: str = "low",
        required_permission_type: str | None = "profile",
        required_permission_action: str | None = "view",
        requires_confirmation: bool = False,
        enabled: bool = True,
    ) -> None:
        self.metadata = AgentToolMetadata(
            name=name,
            description="Fake registry-only tool for unit tests.",
            category=category,
            access_mode=access_mode,
            risk_level=risk_level,
            required_permission_type=required_permission_type,
            required_permission_action=required_permission_action,
            requires_confirmation=requires_confirmation,
            enabled=enabled,
            input_schema_name="FakeToolInput",
            output_schema_name="FakeToolOutput",
            safety_notes=("No business service access in Phase 07.B.",),
        )
        self.executed = False
        self.health_data_read = False

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.executed = True
        return {"ok": True}


if __name__ == "__main__":
    unittest.main()
