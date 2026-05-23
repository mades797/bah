from signal import pause

from bah.display_controller import DisplayController
from bah.audio_controller import AudioController
from bah.inputs import button_1, button_2, button_3, button_4


def main():
    display_controller = DisplayController()
    audio_controller = AudioController(display_controller)

    button_1.when_pressed = audio_controller.handle_next_button
    button_2.when_pressed = audio_controller.handle_back_button
    button_3.when_pressed = audio_controller.handle_up_button
    button_4.when_pressed = audio_controller.handle_down_button

    pause()



if __name__ == '__main__':
    main()