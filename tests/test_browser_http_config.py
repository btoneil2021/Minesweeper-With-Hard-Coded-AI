import pytest

from minesweeper.external.browser.bridge.http_config import BridgeHttpConfig


def test_bridge_http_config_defaults_to_loopback_and_known_port() -> None:
    config = BridgeHttpConfig()

    assert config.host == "127.0.0.1"
    assert config.port == 8765


def test_bridge_http_config_can_override_host_and_port() -> None:
    config = BridgeHttpConfig(host="127.0.0.1", port=9001)

    assert config.host == "127.0.0.1"
    assert config.port == 9001


@pytest.mark.parametrize("host", ["0.0.0.0", "127.0.0.2", "localhost"])
def test_bridge_http_config_rejects_non_loopback_hosts(host: str) -> None:
    with pytest.raises(ValueError, match="host"):
        BridgeHttpConfig(host=host)


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_bridge_http_config_rejects_invalid_ports(port: int) -> None:
    with pytest.raises(ValueError, match="port"):
        BridgeHttpConfig(port=port)
