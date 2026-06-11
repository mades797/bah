# pylint: disable=W0212 (protected-access), R0904 (too-many-public-methods)
"""
Tests module
"""
import json
import time
from unittest import mock

import terminalio
import pytest

from bah.display_controller import DisplayController, DisplayControllerException
# from bah.battery_manager import BatteryManager
from bah.audio_controller import AudioController, AudioControllerState, Media


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
        controller.media_list = [Media(title=f'title-{i}', filename='filename-{i}') for i in range(10)]
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

        Expected result: The mocked media list is read and assigned
        """
        fake_data = {
            'media': [
                {
                    'title': 'title-1',
                    'filename': 'filename-1',
                },
                {
                    'title': 'title-2',
                    'filename': 'filename-2',
                },
                {
                    'title': 'title-3',
                    'filename': 'filename-3',
                },
                {
                    'title': 'title-4',
                    'filename': 'filename-4',
                },
                {
                    'title': 'title-5',
                    'filename': 'filename-5',
                }
            ]
        }
        with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(fake_data))):
            audio_controller._read_media_list()
        assert audio_controller.media_list[0].title == 'title-1'
        assert audio_controller.media_list[0].filename == 'filename-1'
        assert audio_controller.media_list[1].title == 'title-2'
        assert audio_controller.media_list[1].filename == 'filename-2'
        assert audio_controller.media_list[2].title == 'title-3'
        assert audio_controller.media_list[2].filename == 'filename-3'
        assert audio_controller.media_list[3].title == 'title-4'
        assert audio_controller.media_list[3].filename == 'filename-4'
        assert audio_controller.media_list[4].title == 'title-5'
        assert audio_controller.media_list[4].filename == 'filename-5'

    @staticmethod
    def test_read_media_list_no_file():
        """
        Test the `_read_media_list` method when the media file is not found

        Expected result: The mocked media list is not assigned
        """
        with (
            mock.patch.object(
                AudioController,
                'media_list',
                new_callable=mock.PropertyMock
            ) as mock_media_list,
            mock.patch('builtins.open', mock.mock_open()) as mock_open
        ):
            mock_open.side_effect = FileNotFoundError
            AudioController(mock.Mock())
            mock_media_list.assert_not_called()
            mock_open.assert_called_once()

    @staticmethod
    def test_play_current_index(audio_controller):
        """
        Test the `_play_current_index` method

        Expected result: TODO
        """
        audio_controller._current_media_index = 1
        audio_controller.media_list = [
            Media(title='title-1', filename='filename-1'),
            Media(title='title-2', filename='filename-2')
        ]
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

    @staticmethod
    def test_get_media_files(audio_controller):
        """
        Test the `media_files` getter

        Expected result: The media files are returned
        """
        audio_controller._media_list = [
            Media(title='title-1', filename='filename-1'),
            Media(title='title-2', filename='filename-2'),
            Media(title='title-3', filename='filename-3'),
        ]
        assert audio_controller.media_files == ['filename-1', 'filename-2', 'filename-3']


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

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_init_error(mock_displayio) -> None:
        """
        Test the constructor when an error occurs

        Expected result: The constructor raises a DisplayControllerException with the correct error message
        """
        mock_displayio.release_displays.side_effect = IOError('this is an IOError')
        DisplayController._instance = None
        with pytest.raises(DisplayControllerException):
            try:
                DisplayController()
            except DisplayControllerException as error:
                assert str(error) == 'Failed to initialize display controller'
                raise error

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_download_indicator')
    @mock.patch('bah.display_controller.DisplayController.draw_download_indicator')
    def test_download_flash(mock_draw_download_indicator, mock_erase_download_indicator, display_controller) -> None:
        """
        Test the download indicator flashing

        Expected result: The `draw_download_indicator` and `erase_download_indicator` methods are called to produce
        the flashing
        """
        display_controller.start_download_flash()
        time.sleep(2)
        display_controller.stop_download_flash()
        mock_draw_download_indicator.assert_called()
        mock_erase_download_indicator.assert_called()
        assert not display_controller._download_flash_thread.is_alive()

    @staticmethod
    def test_download_flash_stop_redundant(display_controller) -> None:
        """
        This test validates a redundant call to `stop_download_flash` as the object's thread is None

        Expected result: The download_flash thread is not joined
        """
        display_controller._download_flash_thread = None
        display_controller._download_flash_stop = mock.MagicMock()
        display_controller.stop_download_flash()
        display_controller._download_flash_stop.assert_not_called()

    @staticmethod
    def test_download_flash_stop_redundant_2(display_controller) -> None:
        """
        This test validates a redundant call to `stop_download_flash` as the object's stop event is None

        Expected result: The download_flash thread is not joined
        """
        display_controller._download_flash_stop = None
        display_controller._download_flash_thread = mock.MagicMock()
        display_controller.stop_download_flash()
        display_controller._download_flash_thread.assert_not_called()

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_erase_battery(mock_displayio, display_controller) -> None:
        """
        Test `erase_battery` method

        Expected result: A bitmap is created with the right coordinates and written on the display
        """
        display_controller.erase_battery()
        mock_displayio.Bitmap.assert_called_once_with(20, 11, 1)
        mock_displayio.Palette.assert_called_once_with(1)
        mock_displayio.Palette.return_value.__setitem__.assert_has_calls([mock.call(0, 0)])
        mock_displayio.TileGrid.assert_called_once_with(
            mock_displayio.Bitmap.return_value,
            pixel_shader=mock_displayio.Palette.return_value,
            x=108,
            y=0
        )
        display_controller._splash.assert_has_calls([mock.call.append(mock_displayio.TileGrid.return_value)])

    @staticmethod
    @mock.patch('bah.display_controller.Rect')
    @mock.patch('bah.display_controller.Line')
    def test_erase_network(mock_line, mock_rect, display_controller) -> None:
        """
        Test `erase_network` method

        The right bitmap is created to erase the network indicator
        """
        display_controller.erase_network()
        # Network indicator written with no-fill to erase the symbol
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_rect.return_value),
            mock.call(mock_rect.return_value),
            mock.call(mock_rect.return_value),
            mock.call(mock_rect.return_value),
            mock.call(mock_line.return_value),
            mock.call(mock_line.return_value),
        ], any_order=True)

        mock_rect.assert_has_calls([
            mock.call(90, 8, 4, 4, fill=0, outline=0),
            mock.call(94, 6, 4, 6, fill=0, outline=0),
            mock.call(98, 4, 4, 8, fill=0, outline=0),
            mock.call(102, 2, 4, 10, fill=0, outline=0)
        ], any_order=True)
        mock_line.assert_has_calls([
            mock.call(90, 2, 106, 12, color=0),
            mock.call(90, 3, 106, 13, color=0)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_erase_main(mock_displayio, display_controller) -> None:
        """
        Test `erase_main` method

        Expected result: The right bitmap is created to erase the entire main window
        """
        display_controller._splash.reset_mock()
        display_controller.erase_main()
        mock_displayio.Bitmap.assert_called_once_with(128, 48, 1)
        mock_displayio.Palette.assert_called_once_with(1)
        mock_displayio.Palette.return_value.__setitem__.assert_called_once_with(0, 0)
        mock_displayio.TileGrid.assert_called_once_with(
            mock_displayio.Bitmap.return_value,
            pixel_shader=mock_displayio.Palette.return_value,
            x=0,
            y=18
        )
        display_controller._splash.append.assert_called_once_with(mock_displayio.TileGrid.return_value)

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_erase_download_indicator(mock_displayio, display_controller) -> None:
        """
        Test `erase_download_indicator` method

        Expected result: The right bitmap is created to erase the download indicator
        """
        display_controller._splash.reset_mock()
        display_controller.erase_download_indicator()
        mock_displayio.Bitmap.assert_called_once_with(10, 12, 1)
        mock_displayio.Palette.assert_called_once_with(1)
        mock_displayio.Palette.return_value.__setitem__.assert_called_once_with(0, 0)
        mock_displayio.TileGrid.assert_called_once_with(
            mock_displayio.Bitmap.return_value,
            pixel_shader=mock_displayio.Palette.return_value,
            x=74,
            y=0
        )
        display_controller._splash.append.assert_called_once_with(mock_displayio.TileGrid.return_value)

    @staticmethod
    @mock.patch('bah.display_controller.FilledPolygon')
    def test_draw_download_indicator(mock_filled_polygon, display_controller) -> None:
        """
        Test `draw_download_indicator` method

        Expected result: The right FilledPolygon is created to draw the download indicator
        """
        display_controller._splash.reset_mock()
        display_controller.draw_download_indicator()
        display_controller._splash.append.assert_called_once_with(mock_filled_polygon.return_value)
        mock_filled_polygon.assert_called_once_with([
            (77, 2),
            (77, 6),
            (75, 6),
            (79, 10),
            (83, 6),
            (81, 6),
            (81, 2),
        ], outline=0xFFFFFF, fill=0xFFFFFF)

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_25(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 25%

        Expected result: The battery symbol is drawn with the right battery fill
        """
        display_controller._splash.reset_mock()
        display_controller.draw_battery(28)
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_called_once_with(x=108, y=2, height=8, width=4, fill=0xFFFFFF, outline=0xFFFFFF)
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_75(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 75%

        Expected result: The battery symbol is drawn with the right battery fill
        """
        display_controller._splash.reset_mock()
        display_controller.draw_battery(78)
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_called_once_with(x=108, y=2, height=8, width=12, fill=0xFFFFFF, outline=0xFFFFFF)
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_98(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 98%

        Expected result: The battery symbol is drawn with the right battery fill and the battery tip
        """
        display_controller._splash.reset_mock()
        display_controller.draw_battery(98)
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_has_calls([
            mock.call(x=108, y=2, height=8, width=16, fill=0xFFFFFF, outline=0xFFFFFF),
            mock.call(x=122, y=4, height=4, width=4, fill=0xFFFFFF, outline=0xFFFFFF),
        ])
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController._erase')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_1(_mock_rect, _mock_polygon, _mock_erase, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 1%

        Expected result: The battery symbol is drawn
        """
        # TODO
        display_controller._splash.reset_mock()
        display_controller.draw_battery(1)

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.label')
    def test_draw_battery_unknown(mock_label, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery_unknown` method

        Expected result: The "battery unknown" symbol is drawn
        """
        display_controller._splash.reset_mock()
        display_controller.draw_battery_unknown()
        mock_erase_battery.assert_called_once()
        mock_label.Label.assert_called_once_with(terminalio.FONT, text='???', color=0xFFFFFF, x=108, y=4)
        display_controller._splash.append.assert_called_once_with(mock_label.Label.return_value)
