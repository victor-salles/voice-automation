import pytest
from unittest.mock import patch, MagicMock
from assistant_tools import (
    execute_tool,
    describe_tool_call,
    ToolSession,
    execute_run_shell,
    execute_open_app,
    execute_search_web,
)


def test_execute_discover_tools_returns_catalog_listing():
    session = ToolSession()
    result = execute_tool("discover_tools", {}, session)

    assert "Available tools:" in result
    assert "open_app:" in result
    assert "search_web:" in result
    assert "run_shell:" in result
    assert "speak:" in result


def test_execute_select_tools_loads_tools():
    session = ToolSession()
    result = execute_tool("select_tools", {"tool_names": ["speak", "open_app"]}, session)

    assert "Loaded: speak, open_app" in result or "Loaded: open_app, speak" in result
    active_names = [t["name"] for t in session.active_tools]
    assert "speak" in active_names
    assert "open_app" in active_names


def test_execute_unknown_tool_returns_error_message():
    session = ToolSession()
    session.select(["speak"])
    result = execute_tool("unknown_tool", {}, session)

    assert "Error" in result
    assert "not loaded" in result


def test_execute_open_app_calls_subprocess():
    session = ToolSession()
    session.select(["open_app"])

    with patch("assistant_tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = execute_tool("open_app", {"app_name": "Safari"}, session)

        assert "Opened Safari" in result
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["open", "-a", "Safari"]


def test_execute_open_app_handles_failure():
    session = ToolSession()
    session.select(["open_app"])

    with patch("assistant_tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, stderr="Application not found"
        )
        result = execute_tool("open_app", {"app_name": "NonExistent"}, session)

        assert "Failed to open NonExistent" in result
        assert "Application not found" in result


def test_execute_search_web_opens_encoded_url():
    session = ToolSession()
    session.select(["search_web"])

    with patch("assistant_tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        result = execute_tool("search_web", {"query": "python testing"}, session)

        assert "Searching for: python testing" in result
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        # call_args[0][0] is ["open", url]
        cmd_list = call_args[0][0]
        url = cmd_list[1]
        assert "https://www.google.com/search" in url
        assert "python+testing" in url or "python%20testing" in url


def test_execute_run_shell_returns_stdout():
    session = ToolSession()
    session.select(["run_shell"])

    with patch("assistant_tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output content\n", stderr=""
        )
        result = execute_tool("run_shell", {"command": "echo test"}, session)

        assert result == "output content"


def test_execute_run_shell_returns_stderr_on_failure():
    session = ToolSession()
    session.select(["run_shell"])

    with patch("assistant_tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error message\n"
        )
        result = execute_tool("run_shell", {"command": "bad_command"}, session)

        assert "Error: error message" in result


def test_execute_run_shell_handles_timeout():
    session = ToolSession()
    session.select(["run_shell"])

    with patch("assistant_tools.subprocess.run") as mock_run:
        mock_run.side_effect = __import__("subprocess").TimeoutExpired("cmd", 10)
        result = execute_tool("run_shell", {"command": "sleep 100"}, session)

        assert "Error: command timed out after 10 seconds" in result


def test_execute_run_shell_returns_no_output_message_when_empty():
    session = ToolSession()
    session.select(["run_shell"])

    with patch("assistant_tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = execute_tool("run_shell", {"command": "true"}, session)

        assert result == "(no output)"


def test_describe_tool_call_open_app_shows_app_name():
    description = describe_tool_call("open_app", {"app_name": "Safari"})
    assert description == "Open Safari"


def test_describe_tool_call_run_shell_truncates_long_command():
    long_cmd = "a" * 100
    description = describe_tool_call("run_shell", {"command": long_cmd})

    assert description.startswith("Run: ")
    assert "..." in description
    assert len(description) < len(long_cmd)


def test_describe_tool_call_run_shell_short_command():
    description = describe_tool_call("run_shell", {"command": "ls -la"})
    assert description == "Run: ls -la"


def test_describe_tool_call_speak_truncates_long_text():
    long_text = "a" * 100
    description = describe_tool_call("speak", {"text": long_text})

    assert description.startswith("Speak: ")
    assert "..." in description
    assert len(description) < len(long_text)


def test_describe_tool_call_speak_short_text():
    description = describe_tool_call("speak", {"text": "hello"})
    assert description == "Speak: hello"


def test_describe_tool_call_discover_tools():
    description = describe_tool_call("discover_tools", {})
    assert description == "Discover available tools"


def test_describe_tool_call_select_tools():
    description = describe_tool_call(
        "select_tools", {"tool_names": ["speak", "open_app"]}
    )
    assert "Load tools:" in description
    assert "speak" in description
    assert "open_app" in description


def test_describe_tool_call_search_web():
    description = describe_tool_call("search_web", {"query": "python"})
    assert description == "Search: python"


def test_describe_tool_call_unknown_tool():
    description = describe_tool_call("unknown", {"arg": "value"})
    assert "unknown" in description
