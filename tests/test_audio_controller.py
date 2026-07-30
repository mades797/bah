# pylint: disable=W0212 (protected-access), R0904 (too-many-public-methods), R0903 (too-few-public-methods)
"""
Tests module
"""
import json
import threading
import time
from unittest import mock

import pytest

from bah.display_controller import DisplayController
from bah.audio_controller import AudioController, AudioControllerState, EventType, Media


@pytest.fixture(name='audio_controller')
def fixture_audio_controller() -> AudioController:
    """
    Fixture to create an AudioController instance

    :return: AudioController instance
    """
    with (mock.patch('bah.audio_controller.DisplayController'),
          mock.patch('bah.audio_controller.vlc.MediaPlayer'),
          mock.patch('bah.audio_controller.AudioController._read_media_list')):
        controller = AudioController()
        controller.media_list = [Media(title=f'title-{i}', filename=f'filename-{i}') for i in range(10)]
        return controller


@pytest.fixture(scope='function', autouse=True)
def remove_singleton():
    """
    Remove the singleton so that the object is re-created

    :return:
    """
    DisplayController._instance = None
    yield


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
    @mock.patch.object(AudioController, '_display_current_media')
    def test_transition_to_playing(mock_display_current_media, audio_controller):
        """
        Test the `_transition_to_playing` method

        Expected result: TODO
        """
        audio_controller._current_state = AudioControllerState.IDLE
        audio_controller._transition_to_playing()
        assert audio_controller._current_state == AudioControllerState.PLAYING
        mock_display_current_media.assert_called_once()

    @staticmethod
    def test_read_media_list(audio_controller, fake_data):
        """
        Test the `_read_media_list` method

        Expected result: The mocked media list is read and assigned
        """
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
    @mock.patch.object(AudioController, '_increment_media_index')
    @mock.patch.object(AudioController, 'play_pause')
    def test_play_next_idle(
            mock_play_pause,
            mock_increment_media_index,
            audio_controller
    ):
        """
        Test the `play_next` function when the controller is idle

        Expected result: Transition to playing is executed and current media is played
        """
        audio_controller._current_state = AudioControllerState.IDLE
        audio_controller.play_next()
        mock_increment_media_index.assert_not_called()
        mock_play_pause.assert_called_once()
        assert audio_controller.is_idle

    @staticmethod
    @mock.patch.object(AudioController, '_transition_to_idle')
    @mock.patch.object(AudioController, '_increment_media_index')
    @mock.patch.object(AudioController, 'play_pause')
    def test_play_next_playing(
            mock_play_pause,
            mock_increment_media_index,
            mock_transition_to_idle,
            audio_controller
    ):
        """
        Test the `play_next` method when media is playing

        Expected result: The media index is incremented, and the new current media is played.
        """
        audio_controller._current_state = AudioControllerState.PLAYING
        audio_controller.play_next()
        mock_increment_media_index.assert_called_once()
        mock_transition_to_idle.assert_called_once()
        mock_play_pause.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_transition_to_idle')
    @mock.patch.object(AudioController, '_decrement_media_index')
    @mock.patch.object(AudioController, 'play_pause')
    def test_play_previous_idle(
            mock_play_pause,
            mock_decrement_media_index,
            mock_transition_to_idle,
            audio_controller
    ):
        """
        Test the `play_previous` function when the controller is idle

        Expected result: The media index is decremented and the media is played
        """
        audio_controller._current_state = AudioControllerState.IDLE
        audio_controller.play_previous()
        mock_transition_to_idle.assert_called_once()
        mock_decrement_media_index.assert_called_once()
        mock_play_pause.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, '_transition_to_idle')
    @mock.patch.object(AudioController, '_decrement_media_index')
    @mock.patch.object(AudioController, 'play_pause')
    def test_play_previous_playing(
            mock_play_pause,
            mock_decrement_media_index,
            mock_transition_to_idle,
            audio_controller
    ):
        """
        Test the `play_previous` when media is playing

        Expected result: The media index is decremented and the current media is played
        """
        audio_controller._current_state = AudioControllerState.PLAYING
        audio_controller.play_previous()
        mock_decrement_media_index.assert_called_once()
        mock_transition_to_idle.assert_called_once()
        mock_play_pause.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, 'current_volume', new_callable=mock.PropertyMock)
    @mock.patch.object(AudioController, '_display_volume')
    def test_volume_down(mock_display_volume, mock_current_volume, audio_controller):
        """
        Test the `volume_down` function when the volume does not reach the minimum

        Expected result: The volume is decremented and volume is displayed
        """
        mock_current_volume.return_value = 4
        audio_controller._volume_down()
        audio_controller._vlc_player.audio_set_volume.assert_called_once_with(30)
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, 'current_volume', new_callable=mock.PropertyMock)
    @mock.patch.object(AudioController, '_display_volume')
    def test_volume_down_min(mock_display_volume, mock_current_volume, audio_controller):
        """
        Test the `volume_down` function when the volume reaches the minimum

        Expected result: The volume is set to zero and volume is displayed
        """
        mock_current_volume.return_value = 1
        audio_controller._volume_down()
        audio_controller._vlc_player.audio_set_volume.assert_called_once_with(0)
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, 'current_volume', new_callable=mock.PropertyMock)
    @mock.patch.object(AudioController, '_display_volume')
    def test_volume_down_min2(mock_display_volume, mock_current_volume, audio_controller):
        """
        Test the `volume_down` function when the volume is already at minimum

        Expected result: The volume is not set and volume is displayed
        """
        mock_current_volume.return_value = 0
        audio_controller._volume_down()
        audio_controller._vlc_player.audio_set_volume.assert_not_called()
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, 'current_volume', new_callable=mock.PropertyMock)
    @mock.patch.object(AudioController, '_display_volume')
    def test_volume_up(mock_display_volume, mock_current_volume, audio_controller):
        """
        Test the `volume_up` function when the volume does not reach the maximum

        Expected result: The volume is incremented and volume is displayed
        """
        mock_current_volume.return_value = 6
        audio_controller._volume_up()
        audio_controller._vlc_player.audio_set_volume.assert_called_once_with(70)
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, 'current_volume', new_callable=mock.PropertyMock)
    @mock.patch.object(AudioController, '_display_volume')
    def test_volume_up_max(mock_display_volume, mock_current_volume, audio_controller):
        """
        Test the `volume_up` function when the volume reaches the maximum

        Expected result: The volume is set to maximum and volume is displayed
        """
        mock_current_volume.return_value = 9
        audio_controller._volume_up()
        audio_controller._vlc_player.audio_set_volume.assert_called_once_with(100)
        mock_display_volume.assert_called_once()

    @staticmethod
    @mock.patch.object(AudioController, 'current_volume', new_callable=mock.PropertyMock)
    @mock.patch.object(AudioController, '_display_volume')
    def test_volume_up_max2(mock_display_volume, mock_current_volume, audio_controller):
        """
        Test the `volume_up` function when the volume is already at maximum

        Expected result: The volume is not set and volume is displayed
        """
        mock_current_volume.return_value = 10
        audio_controller._volume_up()
        audio_controller._vlc_player.audio_set_volume.assert_not_called()
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

    @staticmethod
    def test_play_pause_while_idle(audio_controller):
        """
        Test the `play_pause` function while the controller is idle

        Expected: The current media is played
        """
        audio_controller._current_state = AudioControllerState.IDLE
        audio_controller.play_pause()
        audio_controller._vlc_instance.media_new.assert_called_once_with('/data/filename-0')
        audio_controller._vlc_player.set_media.assert_called_once_with(
            audio_controller._vlc_instance.media_new.return_value
        )
        audio_controller._vlc_player.play.assert_called_once()
        assert audio_controller.is_playing
        audio_controller._display_controller.write_top_banner.assert_called_once_with('Lecture')
        audio_controller._display_controller.write_main.assert_called_once_with('1: title-0')

    @staticmethod
    def test_play_pause_while_paused(audio_controller):
        """
        Test the `play_pause` function while the controller is paused

        Expected: The current media is played
        """
        audio_controller._current_state = AudioControllerState.PAUSED
        audio_controller._vlc_player.get_time.return_value = 10000
        audio_controller.play_pause()
        audio_controller._vlc_player.set_time.assert_called_once_with(8000)
        audio_controller._vlc_player.play.assert_called_once()
        assert audio_controller.is_playing
        audio_controller._display_controller.write_top_banner.assert_called_once_with('Lecture')
        audio_controller._display_controller.write_main.assert_called_once_with('1: title-0')

    @staticmethod
    def test_play_pause_while_playing(audio_controller):
        """
        Test the `play_pause` function while the controller is playing

        Expected: The current media is paused
        """
        audio_controller._current_state = AudioControllerState.PLAYING
        audio_controller.play_pause()
        audio_controller._vlc_player.pause.assert_called_once()
        assert audio_controller.is_paused
        audio_controller._display_controller.write_top_banner.assert_called_once_with('Pause')

    @staticmethod
    def test_run(audio_controller):
        """
        Test the `run` function when receiving multiple events

        Expected: The events in the queue are properly handled
        """

        calls = []

        def play_pause_side_effect():
            calls.append('play-pause')

        def play_next_side_effect():
            calls.append('play-next')

        def play_previous_side_effect():
            calls.append('play-previous')

        def volume_down_side_effect():
            calls.append('volume-down')

        def volume_up_side_effect():
            calls.append('volume-up')

        with (mock.patch.object(AudioController, 'play_pause') as mock_play_pause,
              mock.patch.object(AudioController, 'play_next') as mock_play_next,
              mock.patch.object(AudioController, 'play_previous') as mock_play_previous,
              mock.patch.object(AudioController, '_volume_down') as mock_volume_down,
              mock.patch.object(AudioController, '_volume_up') as mock_volume_up):
            mock_play_pause.side_effect = play_pause_side_effect
            mock_play_next.side_effect = play_next_side_effect
            mock_play_previous.side_effect = play_previous_side_effect
            mock_volume_down.side_effect = volume_down_side_effect
            mock_volume_up.side_effect = volume_up_side_effect
            audio_controller.event_queue.put(EventType.PLAY_PAUSE_BUTTON)
            audio_controller.event_queue.put(EventType.LEFT_BUTTON)
            audio_controller.event_queue.put(EventType.UP_BUTTON)
            audio_controller.event_queue.put(EventType.END_OF_MEDIA)
            audio_controller.event_queue.put(EventType.RIGHT_BUTTON)
            audio_controller.event_queue.put(EventType.PLAY_PAUSE_BUTTON)
            audio_controller.event_queue.put(EventType.DOWN_BUTTON)
            audio_controller.event_queue.put(EventType.RIGHT_BUTTON)
            audio_controller.event_queue.put(666)
            audio_controller.event_queue.put(EventType.EXIT)
            audio_controller.run()
            assert calls == [
                'play-pause',
                'play-previous',
                'volume-up',
                'play-next',
                'play-next',
                'play-pause',
                'volume-down',
                'play-next',
            ]

    @staticmethod
    def test_run_exists(audio_controller):
        """
        Test that the `run` method exists properly

        Expected: The loop breaks when receiving an exit event
        """
        thread = threading.Thread(target=audio_controller.run)
        thread.start()
        time.sleep(1)
        audio_controller.event_queue.put(EventType.EXIT)
        thread.join()

    @staticmethod
    def test_handle_end_of_media(audio_controller):
        """
        Test the `handle_end_of_media` method

        Expected: A END_OF_MEDIA is put in the queue
        """
        audio_controller.handle_end_of_media(mock.Mock())
        event = audio_controller.event_queue.get(timeout=0.1)
        assert event == EventType.END_OF_MEDIA

    @staticmethod
    def test_handle_play_button(audio_controller):
        """
        Test the `handle_play_button` method

        Expected: A PLAY_PAUSE_BUTTON is put in the queue
        """
        audio_controller.handle_play_button()
        event = audio_controller.event_queue.get(timeout=0.1)
        assert event == EventType.PLAY_PAUSE_BUTTON

    @staticmethod
    def test_handle_next_button(audio_controller):
        """
        Test the `handle_next_button` method

        Expected: A RIGHT_BUTTON is put in the queue
        """
        audio_controller.handle_next_button()
        event = audio_controller.event_queue.get(timeout=0.1)
        assert event == EventType.RIGHT_BUTTON

    @staticmethod
    def test_handle_back_button(audio_controller):
        """
        Test the `handle_back_button` method

        Expected: A LEFT_BUTTON is put in the queue
        """
        audio_controller.handle_back_button()
        event = audio_controller.event_queue.get(timeout=0.1)
        assert event == EventType.LEFT_BUTTON

    @staticmethod
    def test_handle_up_button(audio_controller):
        """
        Test the `handle_up_button` method

        Expected: A UP_BUTTON is put in the queue
        """
        audio_controller.handle_up_button()
        event = audio_controller.event_queue.get(timeout=0.1)
        assert event == EventType.UP_BUTTON

    @staticmethod
    def test_handle_down_button(audio_controller):
        """
        Test the `handle_down_button` method

        Expected: A DOWN_BUTTON is put in the queue
        """
        audio_controller.handle_down_button()
        event = audio_controller.event_queue.get(timeout=0.1)
        assert event == EventType.DOWN_BUTTON
