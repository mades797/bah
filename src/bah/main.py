"""
BAH main module
"""
import logging
from signal import pause

from gpiozero import Button

from bah.battery_manager import BatteryManager
from bah.display_controller import DisplayController
from bah.audio_controller import AudioController
from bah.exceptions import BAHException
from bah.network_sync import NetworkSync


def main() -> None:
    """
    Main entry point

    :return:
    """
    try:
        logging.info('Starting BAH')
        button_1 = Button(27)
        button_2 = Button(22)
        button_3 = Button(12)
        button_4 = Button(19)
        logging.basicConfig(level=logging.INFO)
        display_controller = DisplayController()
        audio_controller = AudioController(display_controller)
        network_sync = NetworkSync(display_controller, audio_controller)
        network_sync.run_async()
        battery_manager = BatteryManager(display_controller)
        battery_manager.run_async()

        button_1.when_pressed = audio_controller.handle_next_button
        button_2.when_pressed = audio_controller.handle_back_button
        button_3.when_pressed = audio_controller.handle_up_button
        button_4.when_pressed = audio_controller.handle_down_button

        pause()
    except BAHException as error:
        logging.exception('Failed to initialize BAH: %s', error)


if __name__ == '__main__':
    main()
