from enum import Enum
import json

from bah.display_controller import DisplayController

class AudioControllerState(Enum):
    IDLE = 0
    PLAYING = 1


class AudioController:
    _welcome_message = '!!Bonjour!!'

    def __init__(self, display_controller: DisplayController = None):
        self._display_controller = display_controller or DisplayController()
        self._media = []
        self._current_media_index = 0
        self._current_state = AudioControllerState.IDLE
        self._current_volume = 0
        self._read_media_list()
        self._display_controller.write_top_banner(self._welcome_message)

    @property
    def is_idle(self):
        return self._current_state == AudioControllerState.IDLE

    @property
    def is_playing(self):
        return self._current_state == AudioControllerState.PLAYING

    def _transition_to_playing(self):
        self._current_state = AudioControllerState.PLAYING
        self._display_volume()

    def _read_media_list(self):
        with open('/data/media.json', 'r', encoding='utf-8') as f:
            self._media = json.loads(f.read())['media']

    def _play_current_index(self):
        self._display_controller.write_main(self._media[self._current_media_index]['title'])

    def _increment_media_index(self):
        if self._current_media_index >= len(self._media) - 1:
            self._current_media_index = 0
        else:
            self._current_media_index += 1

    def _decrement_media_index(self):
        if self._current_media_index == 0:
            self._current_media_index = len(self._media) - 1
        else:
            self._current_media_index -= 1

    def handle_next_button(self):
        if self.is_idle:
            self._transition_to_playing()
        elif self.is_playing:
            self._increment_media_index()
        self._play_current_index()
        self._display_controller.draw_battery(15)

    def handle_back_button(self):
        if self.is_idle:
            self._transition_to_playing()
        elif self.is_playing:
            self._decrement_media_index()
        self._play_current_index()
        self._display_controller.draw_battery(35)

    def handle_up_button(self):
        self._current_volume += 1
        self._display_volume()
        self._display_controller.draw_battery(75)

    def handle_down_button(self):
        self._current_volume -= 1
        self._display_volume()
        self._display_controller.draw_battery(100)

    def _display_volume(self):
        self._display_controller.write_top_banner(f'Volume: {self._current_volume}')
