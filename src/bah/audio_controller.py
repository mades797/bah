"""
BAH audio controller module
"""
from dataclasses import dataclass
from enum import Enum
import json
import logging
import os
import queue

import vlc

from bah.display_controller import DisplayController
from bah.exceptions import BAHException

logger = logging.getLogger('bah-audio-controller')
logger.setLevel(logging.DEBUG)


class EventType(Enum):
    """
    Event type enumeration
    """
    END_OF_MEDIA = 0
    PLAY_PAUSE_BUTTON = 1
    RIGHT_BUTTON = 2
    LEFT_BUTTON = 3
    UP_BUTTON = 4
    DOWN_BUTTON = 5
    EXIT = 6


class AudioControllerException(BAHException):
    """
    AudioController exception
    """


class AudioControllerState(Enum):
    """
    Audio controller states enum
    """
    IDLE = 0
    PLAYING = 1
    PAUSED = 2


@dataclass
class Media:
    """
    Class used to model a media
    """
    title: str
    filename: str


class AudioController:
    """
    Audio controller class
    """
    min_volume = 0
    max_volume = 10
    volume_step = 1

    local_data_dir = '/data'
    local_data_file = os.path.join(local_data_dir, 'media.json')

    def __init__(self, display_controller: DisplayController = None):
        self._display_controller = display_controller or DisplayController()
        self._media_list: list[Media] = []
        self._current_media_index = 0
        self._current_state = AudioControllerState.IDLE
        self._read_media_list()
        self._vlc_player = vlc.MediaPlayer()
        self._vlc_instance = self._vlc_player.get_instance()
        event_manager = self._vlc_player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_end_of_media)
        self.event_queue: queue.Queue[EventType] = queue.Queue()

    @property
    def current_media(self) -> Media:
        """
        Returns current media instance

        :return:
        """
        return self._media_list[self._current_media_index]

    @property
    def current_volume(self) -> int:
        """
        Returns the current volume

        :return:
        """
        vol = self._vlc_player.audio_get_volume()
        logger.debug('Current volume: %s', vol)
        return int(vol / 10)

    @property
    def media_files(self) -> list[str]:
        """
        Get the list of files corresponding to the media list

        :return: List of file names
        """
        return [media.filename for media in self._media_list]

    @property
    def media_list(self) -> list[Media]:
        """
        Get the media list

        :return: media list
        """
        return self._media_list

    @media_list.setter
    def media_list(self, new_media: list[Media]) -> None:
        self._media_list = new_media

    def _read_media_list(self) -> None:
        """
        Read the media list from a file

        :return:
        """
        try:
            with open(self.local_data_file, 'r', encoding='utf-8') as json_file:
                # TODO: Check that files exist
                # TODO: Check that file is valid
                self.media_list = [Media(**media) for media in json.loads(json_file.read())['media']]
        except FileNotFoundError:
            logger.warning('Could not read local media data file')

    @property
    def is_idle(self) -> bool:
        """
        Check if media is currently idle

        :return:
        """
        return self._current_state == AudioControllerState.IDLE

    @property
    def is_paused(self) -> bool:
        """
        Check if current media is paused

        :return:
        """
        return self._current_state == AudioControllerState.PAUSED

    @property
    def is_playing(self) -> bool:
        """
        Determine if media is currently playing

        :return:
        """
        return self._current_state == AudioControllerState.PLAYING

    def _display_current_media(self) -> None:
        self._display_controller.write_main(f'{self._current_media_index + 1}: {self.current_media.title}')

    def _transition_to_playing(self) -> None:
        self._current_state = AudioControllerState.PLAYING
        self._display_controller.write_top_banner('Lecture')
        self._display_current_media()

    def _transition_to_pause(self) -> None:
        self._current_state = AudioControllerState.PAUSED
        self._display_controller.write_top_banner('Pause')

    def _transition_to_idle(self) -> None:
        self._current_state = AudioControllerState.IDLE

    def _play_current_index(self) -> None:
        self._display_controller.write_main(self.media_list[self._current_media_index].title)

    def _increment_media_index(self) -> None:
        if self._current_media_index >= len(self.media_list) - 1:
            self._current_media_index = 0
        else:
            self._current_media_index += 1

    def _decrement_media_index(self) -> None:
        if self._current_media_index == 0:
            self._current_media_index = len(self.media_list) - 1
        else:
            self._current_media_index -= 1

    def rewind(self, seconds: int) -> None:
        """
        Rewind the current media to a previous point by the given number of seconds.

        :param seconds:
        :return:
        """
        current_time = self._vlc_player.get_time()
        self._vlc_player.set_time(current_time - (seconds * 1000))

    def run(self) -> None:
        """
        Run the audio controller

        :return:
        """
        while True:
            try:
                action: EventType = self.event_queue.get(timeout=0.5)
                logger.debug('Action from queue: %s', action)
                match action:
                    case EventType.PLAY_PAUSE_BUTTON:
                        self.play_pause()
                    case EventType.END_OF_MEDIA:
                        self.play_next()
                    case EventType.RIGHT_BUTTON:
                        self.play_next()
                    case EventType.LEFT_BUTTON:
                        self.play_previous()
                    case EventType.DOWN_BUTTON:
                        self._volume_down()
                    case EventType.UP_BUTTON:
                        self._volume_up()
                    case EventType.EXIT:
                        break
                    case _:
                        logger.error('Unknown action: %s', action)
            except queue.Empty:
                continue

    def handle_end_of_media(self, _event: vlc.Event) -> None:
        """
        Handle the end of the current media playback

        :param _event:
        :return:
        """
        self.event_queue.put(EventType.END_OF_MEDIA)

    def handle_play_button(self) -> None:
        """
        Handle play button press

        :return:
        """
        logger.debug('Handling play button press')
        self.event_queue.put(EventType.PLAY_PAUSE_BUTTON)

    def play_pause(self) -> None:
        """
        Play or pause the current media

        :return:
        """
        if self.is_idle:
            vlc_media = self._vlc_instance.media_new(os.path.join(self.local_data_dir, self.current_media.filename))
            self._vlc_player.set_media(vlc_media)
            self._vlc_player.play()
            self._transition_to_playing()
        elif self.is_paused:
            self.rewind(2)
            self._vlc_player.play()
            self._transition_to_playing()
        else:
            self._vlc_player.pause()
            self._transition_to_pause()

    def handle_next_button(self) -> None:
        """
        Handle the next button push

        :return:
        """
        logger.debug('Handling next button press')
        self.event_queue.put(EventType.RIGHT_BUTTON)

    def play_next(self) -> None:
        """
        Play the next media

        :return:
        """
        self._vlc_player.stop()
        if self._current_state != AudioControllerState.IDLE:
            self._increment_media_index()
        self._transition_to_idle()
        self.play_pause()

    def handle_back_button(self) -> None:
        """
        Handle the back button push

        :return:
        """
        logger.debug('Handling back button press')
        self.event_queue.put(EventType.LEFT_BUTTON)

    def play_previous(self) -> None:
        """
        Play the previous media

        :return:
        """
        self._vlc_player.stop()
        self._transition_to_idle()
        self._decrement_media_index()
        self.play_pause()

    def handle_up_button(self) -> None:
        """
        Handle the up button push

        :return:
        """
        logger.debug('Handling up button press')
        self.event_queue.put(EventType.UP_BUTTON)

    def handle_down_button(self) -> None:
        """
        Handle the down button push

        :return:
        """
        logger.debug('Handling down button press')
        self.event_queue.put(EventType.DOWN_BUTTON)

    def _set_volume(self, volume: int) -> None:
        self._vlc_player.audio_set_volume(volume * 10)

    def _volume_up(self) -> None:
        if self.current_volume < self.max_volume:
            self._set_volume(self.current_volume + self.volume_step)
        self._display_volume()

    def _volume_down(self) -> None:
        if self.current_volume > self.min_volume:
            self._set_volume(self.current_volume - self.volume_step)
        self._display_volume()

    def _display_volume(self) -> None:
        self._display_controller.write_top_banner(f'Volume: {self.current_volume}')
