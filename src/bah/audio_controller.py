"""
BAH audio controller module
"""
from enum import Enum
import json

from bah.display_controller import DisplayController


class AudioControllerState(Enum):
    """
    Audio controller states enum
    """
    IDLE = 0
    PLAYING = 1


class AudioController:
    """
    Audio controller class
    """
    _welcome_message = '!!Bonjour!!'
    min_volume = 0
    max_volume = 100
    volume_step = 10

    def __init__(self, display_controller: DisplayController = None):
        self._display_controller = display_controller or DisplayController()
        self._media: list[dict] = []
        self._current_media_index = 0
        self._current_state = AudioControllerState.IDLE
        self._current_volume = 0
        self._read_media_list()
        self._display_controller.write_top_banner(self._welcome_message)

    @property
    def is_idle(self) -> bool:
        """
        Check if media is currently idle

        :return:
        """
        return self._current_state == AudioControllerState.IDLE

    @property
    def is_playing(self) -> bool:
        """
        Determine if media is currently playing

        :return:
        """
        return self._current_state == AudioControllerState.PLAYING

    def _transition_to_playing(self) -> None:
        self._current_state = AudioControllerState.PLAYING
        self._display_volume()

    def _read_media_list(self) -> None:
        with open('/data/media.json', 'r', encoding='utf-8') as f:
            self._media = json.loads(f.read())['media']

    def _play_current_index(self) -> None:
        self._display_controller.write_main(self._media[self._current_media_index]['title'])

    def _increment_media_index(self) -> None:
        if self._current_media_index >= len(self._media) - 1:
            self._current_media_index = 0
        else:
            self._current_media_index += 1

    def _decrement_media_index(self) -> None:
        if self._current_media_index == 0:
            self._current_media_index = len(self._media) - 1
        else:
            self._current_media_index -= 1

    def handle_next_button(self) -> None:
        """
        Handle the next button push

        :return:
        """
        if self.is_idle:
            self._transition_to_playing()
        else:
            self._increment_media_index()
        self._play_current_index()

    def handle_back_button(self) -> None:
        """
        Handle the back button push

        :return:
        """
        if self.is_idle:
            self._transition_to_playing()
        else:
            self._decrement_media_index()
        self._play_current_index()

    def _decrement_volume(self) -> None:
        self._current_volume = max(self._current_volume - self.volume_step, self.min_volume)

    def _increment_volume(self) -> None:
        self._current_volume = min(self._current_volume + self.volume_step, self.max_volume)

    def handle_up_button(self) -> None:
        """
        Handle the up button push

        :return:
        """
        self._increment_volume()
        self._display_volume()

    def handle_down_button(self) -> None:
        """
        Handle the down button push

        :return:
        """
        self._decrement_volume()
        self._display_volume()

    def _display_volume(self) -> None:
        self._display_controller.write_top_banner(f'Volume: {self._current_volume}')
