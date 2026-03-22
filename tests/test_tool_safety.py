import pytest
from assistant_tools import requires_confirmation, SAFE_TOOLS, ASK_TOOLS


def test_speak_does_not_require_confirmation():
    assert not requires_confirmation("speak")


def test_search_web_does_not_require_confirmation():
    assert not requires_confirmation("search_web")


def test_open_app_does_not_require_confirmation():
    assert not requires_confirmation("open_app")


def test_discover_tools_does_not_require_confirmation():
    assert not requires_confirmation("discover_tools")


def test_select_tools_does_not_require_confirmation():
    assert not requires_confirmation("select_tools")


def test_run_shell_requires_confirmation():
    assert requires_confirmation("run_shell")


def test_unknown_tool_does_not_require_confirmation():
    assert not requires_confirmation("unknown_tool")
