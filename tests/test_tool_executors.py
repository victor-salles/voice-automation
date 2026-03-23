import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
import urllib.error

# Ensure scripts directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import tool_executors


class TestRun(unittest.TestCase):
    """Test the _run helper function."""

    @patch("tool_executors.subprocess.run")
    def test_run_success_returns_output_and_true(self, mock_run):
        """Test _run returns (output, True) on success."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="test output\n",
            stderr="",
        )
        output, success = tool_executors._run("test command")
        assert output == "test output"
        assert success is True

    @patch("tool_executors.subprocess.run")
    def test_run_success_strips_output(self, mock_run):
        """Test _run strips whitespace from output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="  output with spaces  \n",
            stderr="",
        )
        output, success = tool_executors._run("test command")
        assert output == "output with spaces"

    @patch("tool_executors.subprocess.run")
    def test_run_success_empty_output_returns_no_output(self, mock_run):
        """Test _run returns '(no output)' when stdout is empty."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        output, success = tool_executors._run("test command")
        assert output == "(no output)"
        assert success is True

    @patch("tool_executors.subprocess.run")
    def test_run_failure_returns_stderr_and_false(self, mock_run):
        """Test _run returns (stderr, False) on non-zero return code."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error message\n",
        )
        output, success = tool_executors._run("test command")
        assert output == "error message"
        assert success is False

    @patch("tool_executors.subprocess.run")
    def test_run_failure_no_stderr_returns_command_failed(self, mock_run):
        """Test _run returns '(command failed)' when no stderr."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="",
        )
        output, success = tool_executors._run("test command")
        assert output == "(command failed)"
        assert success is False

    @patch("tool_executors.subprocess.run")
    def test_run_timeout_returns_timeout_message(self, mock_run):
        """Test _run returns timeout message on TimeoutExpired."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
        output, success = tool_executors._run("test command", timeout=10)
        assert output == "Command timed out"
        assert success is False

    @patch("tool_executors.subprocess.run")
    def test_run_exception_returns_exception_string(self, mock_run):
        """Test _run returns exception message on exception."""
        mock_run.side_effect = ValueError("test exception")
        output, success = tool_executors._run("test command")
        assert "test exception" in output
        assert success is False

    @patch("tool_executors.subprocess.run")
    def test_run_uses_correct_timeout(self, mock_run):
        """Test _run passes timeout to subprocess.run."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        tool_executors._run("test", timeout=30)
        mock_run.assert_called_once()
        assert mock_run.call_args[1]["timeout"] == 30


class TestExtractField(unittest.TestCase):
    """Test the _extract_field helper function."""

    def test_extract_field_basic(self):
        """Test extracting a field from text."""
        text = "name: John\nage: 30\naddress: Main St"
        result = tool_executors._extract_field(text, "age")
        assert result == "30"

    def test_extract_field_with_spaces(self):
        """Test extracting a field with spaces in value."""
        text = "SSID: My WiFi Network\nSignal: -50"
        result = tool_executors._extract_field(text, "SSID")
        assert result == "My WiFi Network"

    def test_extract_field_not_found(self):
        """Test extracting a non-existent field returns None."""
        text = "name: John\nage: 30"
        result = tool_executors._extract_field(text, "email")
        assert result is None

    def test_extract_field_empty_text(self):
        """Test extracting from empty text returns None."""
        result = tool_executors._extract_field("", "field")
        assert result is None

    def test_extract_field_strips_whitespace(self):
        """Test extracted field values are stripped."""
        text = "name:   John   \nage: 30"
        result = tool_executors._extract_field(text, "name")
        assert result == "John"


class TestExecuteGetWeather(unittest.TestCase):
    """Test execute_get_weather function."""

    @patch("tool_executors._run")
    def test_get_weather_auto_detect_success(self, mock_run):
        """Test weather auto-detection with successful first source."""
        mock_run.return_value = ("New York: Sunny +20°C 65% 10 km/h", True)
        result = tool_executors.execute_get_weather("auto")
        assert "Weather for" in result
        assert "New York" in result

    @patch("tool_executors._run")
    def test_get_weather_specific_city_success(self, mock_run):
        """Test weather for specific city."""
        mock_run.return_value = ("London: Cloudy +15°C 70% 15 km/h", True)
        result = tool_executors.execute_get_weather("London")
        assert "Weather for" in result
        assert "London" in result

    @patch("tool_executors._run")
    def test_get_weather_primary_source_fails_fallback_succeeds(self, mock_run):
        """Test fallback when primary source fails."""
        mock_run.side_effect = [
            ("Unknown location", True),  # Primary fails with "Unknown"
            ("+20°C, Sunny", True),      # Fallback succeeds
        ]
        result = tool_executors.execute_get_weather("auto")
        assert "+20°C, Sunny" in result

    @patch("tool_executors._run")
    def test_get_weather_primary_source_error_fallback_succeeds(self, mock_run):
        """Test fallback when primary source returns error."""
        mock_run.side_effect = [
            ("Connection error", False),  # Primary fails
            ("+20°C, Sunny", True),       # Fallback succeeds
        ]
        result = tool_executors.execute_get_weather("auto")
        assert "+20°C, Sunny" in result

    @patch("tool_executors._run")
    def test_get_weather_both_sources_fail(self, mock_run):
        """Test error message when both sources fail."""
        mock_run.side_effect = [
            ("", False),    # Primary fails
            ("", False),    # Fallback fails
        ]
        result = tool_executors.execute_get_weather("auto")
        assert "Could not retrieve weather information" in result


class TestExecuteSetBrightness(unittest.TestCase):
    """Test execute_set_brightness function."""

    @patch("tool_executors._run")
    def test_set_brightness_success(self, mock_run):
        """Test successful brightness setting with brightness CLI."""
        mock_run.return_value = ("", True)
        result = tool_executors.execute_set_brightness(0.75)
        assert "Brightness set to 75%" in result

    @patch("tool_executors._run")
    @patch("tool_executors._osascript")
    def test_set_brightness_clamps_below_zero(self, mock_osascript, mock_run):
        """Test brightness clamped when below 0."""
        mock_run.return_value = ("", True)
        result = tool_executors.execute_set_brightness(-0.5)
        mock_run.assert_called_with("brightness 0.0")
        assert "Brightness set to 0%" in result

    @patch("tool_executors._run")
    @patch("tool_executors._osascript")
    def test_set_brightness_clamps_above_one(self, mock_osascript, mock_run):
        """Test brightness clamped when above 1.0."""
        mock_run.return_value = ("", True)
        result = tool_executors.execute_set_brightness(1.5)
        mock_run.assert_called_with("brightness 1.0")
        assert "Brightness set to 100%" in result

    @patch("tool_executors._run")
    @patch("tool_executors._osascript")
    def test_set_brightness_cli_fails_fallback_attempted(self, mock_osascript, mock_run):
        """Test fallback to AppleScript when brightness CLI fails."""
        mock_run.return_value = ("", False)
        mock_osascript.return_value = ("", False)
        result = tool_executors.execute_set_brightness(0.5)
        # Should have tried to run brightness command
        mock_run.assert_called()
        # Should have tried AppleScript fallback
        mock_osascript.assert_called()
        assert "Could not set brightness directly" in result
        assert "brew install brightness" in result


class TestExecuteSetVolume(unittest.TestCase):
    """Test execute_set_volume function."""

    @patch("tool_executors._osascript")
    def test_set_volume_with_value(self, mock_osascript):
        """Test setting volume to a specific value."""
        mock_osascript.return_value = ("", True)
        result = tool_executors.execute_set_volume(50)
        assert "Volume set to 50%" in result

    @patch("tool_executors._osascript")
    def test_set_volume_mute(self, mock_osascript):
        """Test muting the system."""
        mock_osascript.return_value = ("", True)
        result = tool_executors.execute_set_volume(0, mute=True)
        assert "System audio muted" in result
        mock_osascript.assert_called_once_with("set volume output muted true")

    @patch("tool_executors._osascript")
    def test_set_volume_clamps_at_zero(self, mock_osascript):
        """Test volume clamped at 0."""
        mock_osascript.return_value = ("", True)
        tool_executors.execute_set_volume(-10)
        # Should clamp to 0
        assert mock_osascript.call_args_list[0] == call("set volume output volume 0")

    @patch("tool_executors._osascript")
    def test_set_volume_clamps_at_hundred(self, mock_osascript):
        """Test volume clamped at 100."""
        mock_osascript.return_value = ("", True)
        tool_executors.execute_set_volume(150)
        # Should clamp to 100
        assert mock_osascript.call_args_list[0] == call("set volume output volume 100")

    @patch("tool_executors._osascript")
    def test_set_volume_unmutes_after_setting(self, mock_osascript):
        """Test that setting volume also unmutes."""
        mock_osascript.return_value = ("", True)
        tool_executors.execute_set_volume(75)
        # Should have two calls: set volume, then unmute
        assert mock_osascript.call_count == 2
        assert mock_osascript.call_args_list[1] == call("set volume output muted false")


class TestGetWifiInfo(unittest.TestCase):
    """Test _get_wifi_info function."""

    @patch("tool_executors._run")
    def test_wifi_info_success_with_all_fields(self, mock_run):
        """Test parsing wifi info with SSID, signal, and channel."""
        airport_output = """
SSID: MyNetwork
agrCtlRSSI: -50
agrCtlNoise: -90
channel: 6
"""
        mock_run.return_value = (airport_output, True)
        result = tool_executors._get_wifi_info()
        assert "Connected to MyNetwork" in result
        assert "signal excellent" in result
        assert "-50 dBm" in result
        assert "channel 6" in result

    @patch("tool_executors._run")
    def test_wifi_info_signal_quality_good(self, mock_run):
        """Test signal quality mapping for 'good'."""
        airport_output = """
SSID: TestNet
agrCtlRSSI: -60
agrCtlNoise: -90
channel: 1
"""
        mock_run.return_value = (airport_output, True)
        result = tool_executors._get_wifi_info()
        assert "signal good" in result

    @patch("tool_executors._run")
    def test_wifi_info_signal_quality_fair(self, mock_run):
        """Test signal quality mapping for 'fair'."""
        airport_output = """
SSID: TestNet
agrCtlRSSI: -70
agrCtlNoise: -90
channel: 11
"""
        mock_run.return_value = (airport_output, True)
        result = tool_executors._get_wifi_info()
        assert "signal fair" in result

    @patch("tool_executors._run")
    def test_wifi_info_signal_quality_weak(self, mock_run):
        """Test signal quality mapping for 'weak'."""
        airport_output = """
SSID: TestNet
agrCtlRSSI: -80
agrCtlNoise: -90
channel: 1
"""
        mock_run.return_value = (airport_output, True)
        result = tool_executors._get_wifi_info()
        assert "signal weak" in result

    @patch("tool_executors._run")
    def test_wifi_info_airport_fails_fallback_succeeds(self, mock_run):
        """Test fallback to system_profiler when airport fails."""
        mock_run.side_effect = [
            ("", False),  # airport fails
            ("Current Network: MyNetwork", True),  # fallback succeeds
        ]
        result = tool_executors._get_wifi_info()
        assert "Wi-Fi info:" in result
        assert "Current Network: MyNetwork" in result

    @patch("tool_executors._run")
    def test_wifi_info_both_sources_fail(self, mock_run):
        """Test error when both airport and fallback fail."""
        mock_run.side_effect = [
            ("", False),  # airport fails
            ("", False),  # fallback fails
        ]
        result = tool_executors._get_wifi_info()
        assert "Could not retrieve Wi-Fi information" in result

    @patch("tool_executors._run")
    def test_wifi_info_missing_optional_fields(self, mock_run):
        """Test wifi info when some fields are missing."""
        airport_output = """
SSID: MyNetwork
agrCtlNoise: -90
"""
        mock_run.return_value = (airport_output, True)
        result = tool_executors._get_wifi_info()
        assert "Connected to MyNetwork" in result


class TestGetBatteryInfo(unittest.TestCase):
    """Test _get_battery_info function."""

    @patch("tool_executors._run")
    def test_battery_info_charging(self, mock_run):
        """Test parsing battery percentage and charging status."""
        mock_run.return_value = (
            "75%; charging; till charged at 100%",
            True
        )
        result = tool_executors._get_battery_info()
        assert "Battery at 75%" in result
        assert "charging" in result

    @patch("tool_executors._run")
    def test_battery_info_discharging(self, mock_run):
        """Test parsing discharging status."""
        mock_run.return_value = (
            "42%; discharging",
            True
        )
        result = tool_executors._get_battery_info()
        assert "Battery at 42%" in result
        assert "discharging" in result

    @patch("tool_executors._run")
    def test_battery_info_command_fails(self, mock_run):
        """Test error message when command fails."""
        mock_run.return_value = ("", False)
        result = tool_executors._get_battery_info()
        assert "Could not retrieve battery information" in result

    @patch("tool_executors._run")
    def test_battery_info_no_match(self, mock_run):
        """Test returns raw output when format doesn't match."""
        output = "Battery information unavailable"
        mock_run.return_value = (output, True)
        result = tool_executors._get_battery_info()
        assert output in result


class TestGetDiskInfo(unittest.TestCase):
    """Test _get_disk_info function."""

    @patch("tool_executors._run")
    def test_disk_info_success(self, mock_run):
        """Test parsing disk information."""
        mock_run.return_value = (
            "/dev/disk1s5s1  500G  400G  100G  80% /",
            True
        )
        result = tool_executors._get_disk_info()
        assert "Disk:" in result
        assert "100G free" in result
        assert "500G total" in result
        assert "80% used" in result

    @patch("tool_executors._run")
    def test_disk_info_command_fails(self, mock_run):
        """Test error message when command fails."""
        mock_run.return_value = ("", False)
        result = tool_executors._get_disk_info()
        assert "Could not retrieve disk information" in result

    @patch("tool_executors._run")
    def test_disk_info_insufficient_fields(self, mock_run):
        """Test returns raw output when not enough fields."""
        output = "incomplete output"
        mock_run.return_value = (output, True)
        result = tool_executors._get_disk_info()
        assert output in result


class TestGetIpInfo(unittest.TestCase):
    """Test _get_ip_info function."""

    @patch("tool_executors._run")
    def test_ip_info_both_found(self, mock_run):
        """Test when both local and public IPs are found."""
        mock_run.side_effect = [
            ("192.168.1.100", True),   # local IP
            ("203.0.113.42", True),    # public IP
        ]
        result = tool_executors._get_ip_info()
        assert "Local IP: 192.168.1.100" in result
        assert "Public IP: 203.0.113.42" in result

    @patch("tool_executors._run")
    def test_ip_info_only_local(self, mock_run):
        """Test when only local IP is found."""
        mock_run.side_effect = [
            ("192.168.1.100", True),   # local IP
            ("", False),               # public IP fails
        ]
        result = tool_executors._get_ip_info()
        assert "Local IP: 192.168.1.100" in result
        assert "Public IP" not in result

    @patch("tool_executors._run")
    def test_ip_info_only_public(self, mock_run):
        """Test when only public IP is found."""
        mock_run.side_effect = [
            ("", False),               # local IP fails
            ("203.0.113.42", True),    # public IP
        ]
        result = tool_executors._get_ip_info()
        assert "Public IP: 203.0.113.42" in result
        assert "Local IP" not in result

    @patch("tool_executors._run")
    def test_ip_info_neither_found(self, mock_run):
        """Test error when neither IP is found."""
        mock_run.side_effect = [
            ("", False),   # local IP fails
            ("", False),   # public IP fails
        ]
        result = tool_executors._get_ip_info()
        assert "Could not retrieve IP information" in result


class TestGetSystemVersion(unittest.TestCase):
    """Test _get_system_version function."""

    @patch("tool_executors._run")
    def test_system_version_success(self, mock_run):
        """Test parsing system version information."""
        mock_run.return_value = (
            "ProductName: macOS\nProductVersion: 14.2\nBuildVersion: 23C64",
            True
        )
        result = tool_executors._get_system_version()
        assert "macOS" in result
        assert "14.2" in result
        assert "23C64" in result

    @patch("tool_executors._run")
    def test_system_version_command_fails(self, mock_run):
        """Test error message when command fails."""
        mock_run.return_value = ("", False)
        result = tool_executors._get_system_version()
        assert "Could not retrieve system version" in result


class TestGetMemoryInfo(unittest.TestCase):
    """Test _get_memory_info function."""

    @patch("tool_executors._run")
    def test_memory_info_success(self, mock_run):
        """Test parsing memory information."""
        # 16 GB in bytes
        mock_run.return_value = ("17179869184", True)
        result = tool_executors._get_memory_info()
        assert "Total memory:" in result
        assert "16" in result
        assert "GB" in result

    @patch("tool_executors._run")
    def test_memory_info_command_fails(self, mock_run):
        """Test error message when command fails."""
        mock_run.return_value = ("", False)
        result = tool_executors._get_memory_info()
        assert "Could not retrieve memory information" in result

    @patch("tool_executors._run")
    def test_memory_info_empty_output(self, mock_run):
        """Test error when output is empty."""
        mock_run.return_value = ("", True)
        result = tool_executors._get_memory_info()
        assert "Could not retrieve memory information" in result


class TestGetCpuInfo(unittest.TestCase):
    """Test _get_cpu_info function."""

    @patch("tool_executors._run")
    def test_cpu_info_success(self, mock_run):
        """Test parsing CPU information."""
        mock_run.return_value = ("Apple M1", True)
        result = tool_executors._get_cpu_info()
        assert "CPU:" in result
        assert "Apple M1" in result

    @patch("tool_executors._run")
    def test_cpu_info_command_fails(self, mock_run):
        """Test error message when command fails."""
        mock_run.return_value = ("", False)
        result = tool_executors._get_cpu_info()
        assert "Could not retrieve CPU information" in result

    @patch("tool_executors._run")
    def test_cpu_info_empty_output(self, mock_run):
        """Test error when output is empty."""
        mock_run.return_value = ("", True)
        result = tool_executors._get_cpu_info()
        assert "Could not retrieve CPU information" in result


class TestExecuteGetSystemInfo(unittest.TestCase):
    """Test execute_get_system_info function."""

    @patch("tool_executors._get_wifi_info")
    def test_system_info_wifi_category(self, mock_wifi):
        """Test retrieving wifi category."""
        mock_wifi.return_value = "Connected to MyNetwork"
        result = tool_executors.execute_get_system_info("wifi")
        assert "Connected to MyNetwork" in result

    @patch("tool_executors._get_battery_info")
    def test_system_info_battery_category(self, mock_battery):
        """Test retrieving battery category."""
        mock_battery.return_value = "Battery at 80%, charging"
        result = tool_executors.execute_get_system_info("battery")
        assert "Battery at 80%, charging" in result

    @patch("tool_executors._get_disk_info")
    def test_system_info_disk_category(self, mock_disk):
        """Test retrieving disk category."""
        mock_disk.return_value = "Disk: 100G free of 500G total (80% used)"
        result = tool_executors.execute_get_system_info("disk")
        assert "Disk:" in result

    @patch("tool_executors._get_ip_info")
    def test_system_info_ip_category(self, mock_ip):
        """Test retrieving IP category."""
        mock_ip.return_value = "Local IP: 192.168.1.100. Public IP: 203.0.113.42"
        result = tool_executors.execute_get_system_info("ip")
        assert "IP:" in result

    @patch("tool_executors._get_system_version")
    def test_system_info_system_category(self, mock_system):
        """Test retrieving system category."""
        mock_system.return_value = "macOS 14.2 (23C64)"
        result = tool_executors.execute_get_system_info("system")
        assert "macOS" in result

    @patch("tool_executors._get_memory_info")
    def test_system_info_memory_category(self, mock_memory):
        """Test retrieving memory category."""
        mock_memory.return_value = "Total memory: 16 GB"
        result = tool_executors.execute_get_system_info("memory")
        assert "memory:" in result

    @patch("tool_executors._get_cpu_info")
    def test_system_info_cpu_category(self, mock_cpu):
        """Test retrieving CPU category."""
        mock_cpu.return_value = "CPU: Apple M1"
        result = tool_executors.execute_get_system_info("cpu")
        assert "CPU:" in result

    def test_system_info_unknown_category(self):
        """Test error message for unknown category."""
        result = tool_executors.execute_get_system_info("unknown")
        assert "Unknown category 'unknown'" in result
        assert "Available:" in result
        assert "wifi" in result
        assert "battery" in result
        assert "disk" in result

    def test_system_info_category_case_insensitive(self):
        """Test that category names are case insensitive."""
        with patch("tool_executors._get_wifi_info") as mock_wifi:
            mock_wifi.return_value = "Connected"
            result = tool_executors.execute_get_system_info("WIFI")
            assert "Connected" in result


class TestExecuteManageApp(unittest.TestCase):
    """Test execute_manage_app function."""

    @patch("tool_executors.subprocess.run")
    def test_manage_app_open_success(self, mock_run):
        """Test opening an application successfully."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = tool_executors.execute_manage_app("open", "Safari")
        assert "Opened Safari" in result

    @patch("tool_executors.subprocess.run")
    def test_manage_app_open_failure(self, mock_run):
        """Test failure when opening an application."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Application not found"
        )
        result = tool_executors.execute_manage_app("open", "NonExistent")
        assert "Failed to open NonExistent" in result
        assert "Application not found" in result

    @patch("tool_executors._osascript")
    def test_manage_app_close_success(self, mock_osascript):
        """Test closing an application successfully."""
        mock_osascript.return_value = ("", True)
        result = tool_executors.execute_manage_app("close", "Safari")
        assert "Closed Safari" in result

    @patch("tool_executors._osascript")
    def test_manage_app_close_failure(self, mock_osascript):
        """Test failure when closing an application."""
        mock_osascript.return_value = ("", False)
        result = tool_executors.execute_manage_app("close", "Safari")
        assert "Failed to close Safari" in result

    @patch("tool_executors._run")
    def test_manage_app_check_running(self, mock_run):
        """Test checking if an application is running."""
        mock_run.return_value = ("running", True)
        result = tool_executors.execute_manage_app("check", "Safari")
        assert "Safari is running" in result

    @patch("tool_executors._run")
    def test_manage_app_check_not_running(self, mock_run):
        """Test checking if an application is not running."""
        mock_run.return_value = ("not running", True)
        result = tool_executors.execute_manage_app("check", "Safari")
        assert "Safari is not running" in result

    def test_manage_app_unknown_action(self):
        """Test error message for unknown action."""
        result = tool_executors.execute_manage_app("invalid", "Safari")
        assert "Unknown action 'invalid'" in result
        assert "open, close, or check" in result


class TestExecuteSearchWeb(unittest.TestCase):
    """Test execute_search_web function."""

    @patch("tool_executors.subprocess.run")
    def test_search_web_opens_browser(self, mock_run):
        """Test that search opens browser with encoded query."""
        mock_run.return_value = MagicMock(returncode=0)
        result = tool_executors.execute_search_web("python tutorial")
        assert "Searching for: python tutorial" in result
        # Verify 'open' command was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        # call_args is a list like ["open", "https://www.google.com/search?q=..."]
        assert isinstance(call_args, list)
        assert call_args[0] == "open"
        assert "google.com/search" in call_args[1]
        assert "python" in call_args[1]
        assert "tutorial" in call_args[1]

    @patch("tool_executors.subprocess.run")
    def test_search_web_encodes_special_characters(self, mock_run):
        """Test that special characters are encoded."""
        mock_run.return_value = MagicMock(returncode=0)
        tool_executors.execute_search_web("hello world!")
        call_args = mock_run.call_args[0][0]
        # call_args is a list like ["open", "https://...?q=..."]
        url = call_args[1]
        # URL should have encoded characters
        assert "search?q=" in url
        # Should not have raw spaces in query
        query_part = url.split("?q=")[1]
        assert " " not in query_part


class TestExecuteRunShell(unittest.TestCase):
    """Test execute_run_shell function."""

    @patch("tool_executors._run")
    def test_run_shell_success(self, mock_run):
        """Test running a shell command successfully."""
        mock_run.return_value = ("command output", True)
        result = tool_executors.execute_run_shell("echo hello")
        assert "command output" in result

    @patch("tool_executors._run")
    def test_run_shell_failure(self, mock_run):
        """Test shell command failure returns stderr."""
        mock_run.return_value = ("command not found", False)
        result = tool_executors.execute_run_shell("nonexistent_cmd")
        assert "command not found" in result

    @patch("tool_executors._run")
    def test_run_shell_timeout(self, mock_run):
        """Test shell command timeout."""
        mock_run.return_value = ("Command timed out", False)
        result = tool_executors.execute_run_shell("sleep 1000")
        assert "Command timed out" in result


if __name__ == "__main__":
    unittest.main()
