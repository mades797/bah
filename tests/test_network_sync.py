# pylint: disable=W0212 (protected-access), R0904 (too-many-public-methods), R0903 (too-few-public-methods)
"""
Test module for NetworkSync
"""
import json
from unittest import mock

import pytest

from bah.network_sync import NetworkSync


@pytest.fixture(name='network_sync')
def fixture_network_sync() -> NetworkSync:
    """
    Fixture to create a NetworkSync instance with the network and file interface mocked

    :return: DisplayController instance
    """
    with (
        mock.patch('bah.display_controller.displayio'),
        mock.patch('bah.display_controller.I2CDisplayBus'),
        mock.patch('bah.display_controller.adafruit_displayio_ssd1306'),
    ):
        return NetworkSync(mock.MagicMock(), mock.MagicMock())


class TestNetworkSync:
    """
    Test class for the NetworkSync class
    """

    @staticmethod
    @mock.patch.object(NetworkSync, 'handle_remote_media_list')
    def test_read_remote_media(mock_handle_remote_media_list, network_sync, fake_data) -> None:
        """
        Test the `read_remote_media` method

        Expected result: The `handle_remote_media_list` is called with the parsed data
        """
        with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(fake_data))):
            network_sync.read_remote_media()
            mock_handle_remote_media_list.assert_called_once_with(fake_data)
