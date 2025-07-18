import pytest
from backend.app.services.network_monitor import _discover_and_update
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_get_all_devices():
    with patch("backend.app.services.network_monitor.get_all_devices") as mock:
        mock.return_value = [
            {"mac": "00:11:22:33:44:55", "online": True, "last_seen": None, "name": None, "hostname": None,
             "vendor": None, "ip": "192.168.0.2"},
            {"mac": "66:77:88:99:AA:BB", "online": False, "last_seen": None, "name": None, "hostname": None,
             "vendor": None, "ip": "192.168.0.3"},
        ]
        yield mock


@pytest.fixture
def mock_mark_offline():
    with patch("backend.app.services.network_monitor.mark_offline") as mock:
        yield mock


@pytest.fixture
def mock_add_alert():
    with patch("backend.app.services.network_monitor.add_alert") as mock:
        yield mock


@pytest.fixture
def mock_upsert_device():
    with patch("backend.app.services.network_monitor.upsert_device") as mock:
        yield mock


@pytest.fixture
def mock_get_default_gateway_subnet():
    with patch("backend.app.services.network_monitor.get_default_gateway_subnet") as mock:
        mock.return_value = "192.168.0.0/24"
        yield mock


@pytest.fixture
def mock_srp():
    with patch("backend.app.services.network_monitor.srp") as mock:
        mock.return_value = [
            MagicMock(hwsrc="00:11:22:33:44:66", psrc="192.168.0.5"),
        ], None
        yield mock


@pytest.fixture
def mock_do_lookup():
    with patch("backend.app.services.network_monitor._do_lookup") as mock:
        mock.return_value = ("00:11:22:33:44:66", "192.168.0.5", "mock_hostname", "mock_vendor")
        yield mock


def test_discover_and_update_no_gateway(mock_get_all_devices, mock_get_default_gateway_subnet):
    mock_get_default_gateway_subnet.return_value = None

    result = _discover_and_update()

    assert len(result) == len(mock_get_all_devices.return_value)


def test_discover_and_update_online_device(mock_get_all_devices, mock_mark_offline, mock_add_alert, mock_upsert_device,
                                           mock_get_default_gateway_subnet, mock_srp, mock_do_lookup):
    result = _discover_and_update()

    assert mock_upsert_device.called
    assert mock_add_alert.called
    assert mock_mark_offline.called
    assert len(result) == len(mock_get_all_devices.return_value)


def test_discover_and_update_new_device(mock_get_all_devices, mock_add_alert, mock_upsert_device, mock_srp,
                                        mock_do_lookup):
    new_device_mac = "00:11:22:33:44:66"
    new_device_ip = "192.168.0.5"
    mock_do_lookup.return_value = (new_device_mac, new_device_ip, "new_hostname", "new_vendor")

    _discover_and_update()

    mock_add_alert.assert_any_call("new_device", new_device_mac, new_device_ip,
                                   "New device detected: 00:11:22:33:44:66 @ new_hostname")
    mock_upsert_device.assert_called_with(new_device_mac, new_device_ip, "new_hostname", "new_vendor")


def test_discover_and_update_offline_device(mock_get_all_devices, mock_mark_offline, mock_add_alert,
                                            mock_get_default_gateway_subnet, mock_srp):
    mock_get_all_devices.return_value[0]["online"] = True
    mock_srp.return_value = []

    _discover_and_update()

    mock_mark_offline.assert_called()
    mock_add_alert.assert_any_call("device_offline", "00:11:22:33:44:55", "192.168.0.2",
                                   "Device went offline: 00:11:22:33:44:55 @ None")
