from clean_for_tts import expand_versions


def test_expand_versions_v_prefix_two_parts():
    assert expand_versions("upgrade to v3.12") == "upgrade to version 3 point 12"


def test_expand_versions_v_prefix_three_parts():
    assert expand_versions("released v1.0.0") == "released version 1 point 0 point 0"


def test_expand_versions_v_prefix_four_parts():
    assert expand_versions("build v1.2.3.4") == "build version 1 point 2 point 3 point 4"


def test_expand_versions_three_part_standalone():
    assert expand_versions("version 3.12.1 is out") == "version 3 point 12 point 1 is out"


def test_expand_versions_four_part_standalone():
    assert expand_versions("3.12.1.4 released") == "3 point 12 point 1 point 4 released"


def test_expand_versions_python_prefix():
    assert expand_versions("Python 3.9") == "Python 3 point 9"


def test_expand_versions_node_prefix():
    assert expand_versions("Node 18.0") == "Node 18 point 0"


def test_expand_versions_macos_prefix():
    assert expand_versions("macOS 14.4") == "macOS 14 point 4"


def test_expand_versions_docker_prefix():
    assert expand_versions("Docker 24.0") == "Docker 24 point 0"


def test_expand_versions_plain_decimal_not_expanded():
    assert expand_versions("value is 3.14") == "value is 3.14"


def test_expand_versions_probability_not_expanded():
    assert expand_versions("probability 0.5") == "probability 0.5"


def test_expand_versions_no_versions_unchanged():
    assert expand_versions("plain text here") == "plain text here"


def test_expand_versions_empty_string():
    assert expand_versions("") == ""
