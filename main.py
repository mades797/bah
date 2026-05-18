from signal import pause

from src.bah.display_controller import DisplayController


def say_hello():
    controller = DisplayController()
    controller.write_top_banner('Bonjour!')
    pause()


if __name__ == '__main__':
    say_hello()
