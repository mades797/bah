"""
DisplayController module
"""
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import board
import displayio
from i2cdisplaybus import I2CDisplayBus
import terminalio


PIXEL_FILL = 0xFFFFFF
PIXEL_NO_FILL = 0x0


class DisplayController:
    """
    Class implementing the display controller interface.
    """

    display_width = 128
    display_height = 64
    top_banner_height = 16

    def __init__(self):
        displayio.release_displays()
        i2c = board.I2C()
        display_bus = I2CDisplayBus(i2c, device_address=0x3C)
        display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=self.display_width, height=self.display_height)
        self._splash = displayio.Group()
        display.root_group = self._splash
        self.button_press_counter = 0
        self.write_top_banner(f'Nombre: {self.button_press_counter}')

    def erase_top_banner(self):
        """
        Erase the top banner

        :return:
        """
        inner_bitmap = displayio.Bitmap(self.display_width, self.top_banner_height, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = PIXEL_NO_FILL
        inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=0, y=0)
        self._splash.append(inner_sprite)

    def write_top_banner(self, message):
        """
        Write a message on the top banner

        :param message:
        :return:
        """
        self.erase_top_banner()
        text_area = label.Label(terminalio.FONT, text=message, color=PIXEL_FILL, x=2, y=2)
        self._splash.append(text_area)
