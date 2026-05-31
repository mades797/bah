# pylint: disable=W0212 (protected-access), R0904 (too-many-public-methods)
"""
Tests module
"""
import json
from unittest import mock

import pytest

from bah.display_controller import DisplayController
# from bah.battery_manager import BatteryManager
from bah.audio_controller import AudioController, AudioControllerState
# from bah.task_scheduler import TaskScheduler, Task


@pytest.fixture(name='audio_controller')
def fixture_audio_controller() -> AudioController:
    """
    Fixture to create an AudioController instance

    :return: AudioController instance
    """
    with (mock.patch('bah.audio_controller.DisplayController'),
          mock.patch('bah.audio_controller.AudioController._read_media_list')):
        controller = AudioController()
        controller._media = [{'title': f'audio-{i}'} for i in range(10)]
        return controller


@pytest.fixture(name='display_controller')
def fixture_display_controller() -> DisplayController:
    """
    Fixture to create a DisplayController instance with the actual interface to the display mocked

    :return: DisplayController instance
    """
    with (
        mock.patch('bah.display_controller.displayio'),
        mock.patch('bah.display_controller.board'),
        mock.patch('bah.display_controller.I2CDisplayBus'),
        mock.patch('bah.display_controller.adafruit_displayio_ssd1306'),
    ):
        return DisplayController()


class TestAudioController:
    """
    test class for AudioController class
    """

    @staticmethod
    def test_is_idle(audio_controller):
        """
        Test the `is_idle` method when media is idle

        Expected result: returns True
        """
        audio_controller._current_state = AudioControllerState.IDLE
        assert audio_controller.is_idle

    @staticmethod
    def test_is_not_idle(audio_controller):
        """
        Test the `is_idle` method when media is not idle

        Expected result: returns False
        """
        audio_controller._current_state = AudioControllerState.PLAYING
        assert not audio_controller.is_idle

    @staticmethod
    def test_is_playing(audio_controller):
        """
        Test the `is_playing` method when media is playing

        Expected result: returns True
        """
        audio_controller._current_state = AudioControllerState.PLAYING
        assert audio_controller.is_playing

    @staticmethod
    def test_is_not_playing(audio_controller):
        """
        Test the `is_playing` method when media is not playing

        Expected result: returns False
        """
        audio_controller._current_state = AudioControllerState.IDLE
        assert not audio_controller.is_playing

    @staticmethod
    @mock.patch.object(AudioController, '_display_volume')
    def test_transition_to_playing(mock_display_volume, audio_controller):
        """
        Test the `_transition_to_playing` method

        Expected result: TODO
        """
        audio_controller._current_state = AudioControllerState.IDLE
        audio_controller._transition_to_playing()
        assert audio_controller._current_state == AudioControllerState.PLAYING
        mock_display_volume.assert_called_once()

    @staticmethod
    def test_read_media_list(audio_controller):
        """
        Test the `_read_media_list` method

        Expected result: The mocked media list is read.
        """
        fake_data = {
            'media': [
                {
                    'title': 'title-1'
                },
                {
                    'title': 'title-2'
                },
                {
                    'title': 'title-3'
                },
                {
                    'title': 'title-4'
                },
                {
                    'title': 'title-5'
                }
            ]
        }
        with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(fake_data))):
            audio_controller._read_media_list()
        assert audio_controller._media == fake_data['media']

    @staticmethod
    def test_play_current_index(audio_controller):
        """
        Test the `_play_current_index` method

        Expected result: TODO
        """
        audio_controller._current_media_index = 1
        audio_controller._media = [{'title': 'title-1'}, {'title': 'title-2'}]
        audio_controller._play_current_index()
        audio_controller._display_controller.write_main.assert_called_with('title-2')

    @staticmethod
    def test_increment_media_index(audio_controller):
        """
        Test the `_increment_media_index` when the index does not point to the end of the list.

        Expected result: The index is incremented.
        """
        audio_controller._current_media_index = 1
        audio_controller._increment_media_index()
        assert audio_controller._current_media_index == 2

    @staticmethod
    def test_increment_media_index_end(audio_controller):
        """
        Test the `_increment_media_index` when the index points to the end of the list.

        Expected result: The index should point to the start of the list.
        """
        audio_controller._current_media_index = 9
        audio_controller._increment_media_index()
        assert audio_controller._current_media_index == 0

    @staticmethod
    def test_decrement_media_index(audio_controller):
        """
        Test the `_decrement_media_index` when the index is not at the start of the list

        Expected result: The media index is decremented.
        """
        audio_controller._current_media_index = 4
        audio_controller._decrement_media_index()
        assert audio_controller._current_media_index == 3

    @staticmethod
    def test_decrement_media_index_start(audio_controller):
        """
        Test the `_decrement_media_index` method when the current media index points to the start of the audio list.

        Expected result: The media index will point to the start of the audio list.
        """
        audio_controller._current_media_index = 0
        audio_controller._decrement_media_index()
        assert audio_controller._current_media_index == 9

    @staticmethod
    @mock.patch.object(AudioController, '_transition_to_playing')
    @mock.patch.object(AudioController, '_increment_media_index')
    @mock.patch.object(AudioController, '_play_current_index')
    def test_handle_next_button_idle(
            mock_play_current_index,
            mock_increment_media_index,
            mock_transition_to_playing,
            audio_controller
    ):
        """
        Test the `handle_next_button` function when the controller is idle

        Expected result: Transition to playing is executed and current media is played
        """
        audio_controller._current_state = AudioControllerState.IDLE
        audio_controller.handle_next_button()
        mock_transition_to_playing.assert_called_once()
        mock_increment_media_index.assert_not_called()
        mock_play_current_index.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_transition_to_playing')
    @mock.patch.object(AudioController, '_increment_media_index')
    @mock.patch.object(AudioController, '_play_current_index')
    def test_handle_next_button_playing(
            mock_play_current_index,
            mock_increment_media_index,
            mock_transition_to_playing,
            audio_controller
    ):
        """
        Test the `handle_next_button` method when media is playing

        Expected result: The media index is incremented, and the new current media is played.
        """
        audio_controller._current_state = AudioControllerState.PLAYING
        audio_controller.handle_next_button()
        mock_increment_media_index.assert_called_once()
        mock_transition_to_playing.assert_not_called()
        mock_play_current_index.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_transition_to_playing')
    @mock.patch.object(AudioController, '_decrement_media_index')
    @mock.patch.object(AudioController, '_play_current_index')
    def test_handle_back_button_idle(
            mock_play_current_index,
            mock_decrement_media_index,
            mock_transition_to_playing,
            audio_controller
    ):
        """
        Test the `handle_back_button` function when the controller is idle

        Expected result: Transition to playing is executed and current media is played
        """
        audio_controller._current_state = AudioControllerState.IDLE
        audio_controller.handle_back_button()
        mock_transition_to_playing.assert_called_once()
        mock_decrement_media_index.assert_not_called()
        mock_play_current_index.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_transition_to_playing')
    @mock.patch.object(AudioController, '_decrement_media_index')
    @mock.patch.object(AudioController, '_play_current_index')
    def test_handle_back_button_playing(
            mock_play_current_index,
            mock_decrement_media_index,
            mock_transition_to_playing,
            audio_controller
    ):
        """
        Test the `handle_back_button` when media is playing

        Expected result: The media index is incremented and the current media is played
        """
        audio_controller._current_state = AudioControllerState.PLAYING
        audio_controller.handle_back_button()
        mock_decrement_media_index.assert_called_once()
        mock_transition_to_playing.assert_not_called()
        mock_play_current_index.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_display_volume')
    def test_handle_down_button(mock_display_volume, audio_controller):
        """
        Test the `handle_down_button` function when the volume does not reach the minimum

        Expected result: The volume is decremented and volume is displayed
        """
        audio_controller._current_volume = 40
        audio_controller.handle_down_button()
        assert audio_controller._current_volume == 30
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_display_volume')
    def test_handle_down_button_min(mock_display_volume, audio_controller):
        """
        Test the `handle_down_button` function when the volume reaches the minimum

        Expected result: The volume is set to zero and volume is displayed
        """
        audio_controller._current_volume = 5
        audio_controller.handle_down_button()
        assert audio_controller._current_volume == 0
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_display_volume')
    def test_handle_down_button_min2(mock_display_volume, audio_controller):
        """
        Test the `handle_down_button` function when the volume is already at minimum

        Expected result: The volume is set to zero and volume is displayed
        """
        audio_controller._current_volume = 0
        audio_controller.handle_down_button()
        assert audio_controller._current_volume == 0
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_display_volume')
    def test_handle_up_button(mock_display_volume, audio_controller):
        """
        Test the `handle_up_button` function when the volume does not reach the maximum

        Expected result: The volume is incremented and volume is displayed
        """
        audio_controller._current_volume = 60
        audio_controller.handle_up_button()
        assert audio_controller._current_volume == 70
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_display_volume')
    def test_handle_up_button_max(mock_display_volume, audio_controller):
        """
        Test the `handle_up_button` function when the volume reaches the maximum

        Expected result: The volume is set to maximum and volume is displayed
        """
        audio_controller._current_volume = 95
        audio_controller.handle_up_button()
        assert audio_controller._current_volume == 100
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_display_volume')
    def test_handle_up_button_max2(mock_display_volume, audio_controller):
        """
        Test the `handle_up_button` function when the volume is already at maximum

        Expected result: The volume is set to maximum and volume is displayed
        """
        audio_controller._current_volume = 100
        audio_controller.handle_up_button()
        assert audio_controller._current_volume == 100
        mock_display_volume.assert_called_once()

    @staticmethod
    def test_display_volume(audio_controller):
        """
        Test the `display_volume` method

        Expected result: TODO
        """
        audio_controller._display_volume()
        audio_controller._display_controller.write_top_banner.assert_called()


class TestDisplayController:
    """
    Test class for DisplayController class
    """

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController._erase')
    def test_erase_top_banner(mock_erase, display_controller):
        """
        Test `erase_top_banner` method

        Expected result: The `_erase` method is called with the right arguments
        """
        display_controller.erase_top_banner()
        mock_erase.assert_called_once_with(DisplayController.display_width, DisplayController.top_banner_height)

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController._erase')
    def test_erase_all(mock_erase, display_controller):
        """
        Test `erase_all` method

        Expected result: The `_erase` method is called with the right arguments
        """
        display_controller.erase_all()
        mock_erase.assert_called_once_with(DisplayController.display_width, DisplayController.display_height)
