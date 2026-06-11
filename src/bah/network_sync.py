"""
NetworkSync main module
"""
import json
import logging
import os
import re
import shutil
import subprocess

from bah.audio_controller import AudioController, Media
from bah.display_controller import DisplayController
from bah.exceptions import BAHException
from bah.task_scheduler import TaskScheduler, Task


class NetworkSyncError(BAHException):
    """
    NetworkSyncError
    """


class NetworkSync(TaskScheduler):
    """
    NetworkSync main class. This class handles the audio file synchronization through the network.
    """

    network_ssid = 'avada kedavra'
    remote_data_dir = '/mnt'
    remote_data_file = os.path.join(remote_data_dir, 'media.json')

    @property
    def media_files(self) -> list[str]:
        """
        Media file list

        :return:
        """
        return self._audio_controller.media_files

    def __init__(self, display_controller: DisplayController, audio_controller: AudioController) -> None:
        super().__init__()
        self._display_controller = display_controller
        self._audio_controller = audio_controller
        self._tasks = [
            Task(
                'check-network',
                5,
                self.is_connected,
                self.set_network_indicator,
            ),
            Task(
                'read-remote-media',
                1,
                self.read_remote_media,
            )
        ]
        self._connected = False
        self.read_remote_media()

    def _sync_media(self, remote_media: dict[str, list]) -> None:
        new_media_list = [Media(media['title'], media['filename']) for media in remote_media['media']]
        files_to_copy = []
        for media in new_media_list:
            if not os.path.isfile(os.path.join(self.remote_data_dir, media.filename)):
                raise NetworkSyncError(f'Could not find media file in remote media directory: {media.filename}')
            if not os.path.isfile(os.path.join(self._audio_controller.local_data_dir, media.filename)):
                files_to_copy.append(media.filename)
        if files_to_copy:
            self._display_controller.start_download_flash()
            for file in files_to_copy:
                shutil.copy(
                    os.path.join(self.remote_data_dir, file),
                    os.path.join(self._audio_controller.local_data_dir, file)
                )
            shutil.copy(self.remote_data_file, self._audio_controller.local_data_file)
            self._display_controller.stop_download_flash()
        self._audio_controller.media_list = new_media_list

    def handle_remote_media_list(self, remote_media_list: dict[str, list]) -> None:
        """
        Handle the remote media list

        :param remote_media_list:
        :return:
        """
        # Check if there is a difference between the remote and local media lists
        if [remote_media['filename'] for remote_media in remote_media_list['media']] != self.media_files:
            self._sync_media(remote_media_list)

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    def read_remote_media(self) -> None:
        """
        Read the remote media definitions

        :return:
        """
        try:
            with open(self.remote_data_file, 'r', encoding='utf-8') as file:
                # TODO: Check that file is valid
                self.handle_remote_media_list(json.loads(file.read()))
        except OSError as error:
            if (
                error.errno == 2 and
                error.strerror == 'No such file or directory' and
                error.filename == self.remote_data_file
            ):
                logging.warning('Failed to read remote media file: %s. Is the remote drive mounted?', error.filename)
            else:
                raise

    def set_network_indicator(self, connected: bool) -> None:
        """
        Set the network indicator

        :param connected: If the network is connected or not
        :return:
        """
        logging.debug('Setting network indicator. Connected: %s', connected)
        if connected != self._connected:
            self._display_controller.erase_network()
        if connected:
            self._display_controller.draw_network()
        else:
            self._display_controller.draw_no_network()
        self._connected = connected

    @classmethod
    def is_connected(cls) -> bool:
        """
        Checks if the network is connected.

        :return:
        """
        logging.debug('Checking if network is connected.')
        result = subprocess.run(['iw', 'dev', 'wlan0', 'link'], capture_output=True, text=True, check=True)
        return re.search(r'SSID:\s+' + cls.network_ssid + r'\s*', result.stdout) is not None
