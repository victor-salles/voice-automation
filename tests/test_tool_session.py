import pytest
from assistant_tools import (
    TOOL_CATALOG,
    ToolSession,
    DISCOVER_TOOL,
    SELECT_TOOL,
    SAFE_TOOLS,
)


def test_initial_active_tools_contains_only_discover_and_select():
    session = ToolSession()
    active = session.active_tools
    names = [t["name"] for t in active]
    assert names == ["discover_tools", "select_tools"]


def test_discover_lists_all_catalog_tools_with_summaries():
    session = ToolSession()
    discover_result = session.discover()

    assert "Available tools:" in discover_result
    for tool_name in TOOL_CATALOG.keys():
        assert tool_name in discover_result
        entry = TOOL_CATALOG[tool_name]
        assert entry["summary"] in discover_result


def test_discover_shows_safety_tier_for_each_tool():
    session = ToolSession()
    discover_result = session.discover()

    for tool_name in TOOL_CATALOG.keys():
        if tool_name in SAFE_TOOLS:
            assert f"- {tool_name}: " in discover_result
            assert "(auto-approved)" in discover_result
        else:
            assert f"- {tool_name}: " in discover_result
            assert "(requires confirmation)" in discover_result


def test_select_loads_requested_tools_into_active_set():
    session = ToolSession()
    result = session.select(["open_app", "speak"])

    active_names = [t["name"] for t in session.active_tools]
    assert "open_app" in active_names
    assert "speak" in active_names
    assert "discover_tools" in active_names
    assert "select_tools" in active_names


def test_select_returns_loaded_tool_names():
    session = ToolSession()
    result = session.select(["open_app", "run_shell"])

    assert "Loaded: open_app, run_shell" in result


def test_select_reports_unknown_tool_names():
    session = ToolSession()
    result = session.select(["nonexistent_tool", "open_app"])

    assert "Unknown: nonexistent_tool" in result
    assert "Loaded: open_app" in result


def test_select_ignores_duplicate_selections():
    session = ToolSession()
    session.select(["open_app"])
    result = session.select(["open_app"])

    active_names = [t["name"] for t in session.active_tools]
    open_app_count = sum(1 for t in active_names if t == "open_app")
    assert open_app_count == 1


def test_active_tools_includes_meta_tools_plus_selected():
    session = ToolSession()
    session.select(["search_web", "speak"])

    active = session.active_tools
    names = [t["name"] for t in active]

    assert "discover_tools" in names
    assert "select_tools" in names
    assert "search_web" in names
    assert "speak" in names
    assert len(names) == 4


def test_selecting_all_tools_makes_all_active():
    session = ToolSession()
    all_tool_names = list(TOOL_CATALOG.keys())
    session.select(all_tool_names)

    active = session.active_tools
    active_names = [t["name"] for t in active]

    for tool_name in all_tool_names:
        assert tool_name in active_names
