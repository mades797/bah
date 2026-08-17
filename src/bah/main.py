"""
BAH main module
"""
import logging
import time

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
    logger = logging.getLogger('bah-main')
    try:
        logger.info('Starting BAH')
        button_1 = Button(13)
        button_4 = Button(27)
        button_5 = Button(22)
        button_3 = Button(26)
        button_2 = Button(6)
        headphone = Button(25, pull_up=True)
        logger.setLevel(logging.INFO)
        display_controller = DisplayController()
        try:
            # If a failure occurs beyond this point, we can display an error on the display
            audio_controller = AudioController(display_controller)
            button_1.when_pressed = audio_controller.handle_play_button
            button_2.when_pressed = audio_controller.handle_next_button
            button_3.when_pressed = audio_controller.handle_back_button
            button_4.when_pressed = audio_controller.handle_up_button
            button_5.when_pressed = audio_controller.handle_down_button
            audio_controller.register_headphone_button(headphone)
            network_sync = NetworkSync(display_controller, audio_controller)
            network_sync.run_async()
            battery_manager = BatteryManager(display_controller)
            battery_manager.run_async()
            while not network_sync.initialized or not battery_manager.initialized:
                time.sleep(0.5)
            display_controller.write_top_banner('Prêt')

            audio_controller.run()
        except BAHException:
            display_controller.write_top_banner('Erreur!')
            raise
    except BAHException as error:
        logger.error('Failed to initialize BAH: %s', error)


if __name__ == '__main__':
    main()
