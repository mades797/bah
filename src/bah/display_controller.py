"""
DisplayController module
"""
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import board
import displayio
from i2cdisplaybus import I2CDisplayBus
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.polygon import Polygon


PIXEL_FILL = 0xFFFFFF
PIXEL_NO_FILL = 0x0


class DisplayController:
    """
    Class implementing the display controller interface.
    """

    display_width = 128
    display_height = 64
    top_banner_height = 16
    main_window_top = 21
    main_window_height = display_height - top_banner_height

    # Top left message
    top_message_end_x = 106

    # Battery charge indication
    bat_main_rect_start_x = 108
    bat_main_rect_end_x = 124
    bat_main_rect_start_y = 2
    bat_main_rect_end_y = 10
    bat_tip_start_y = 4
    bat_tip_end_y = 8
    bat_tip_length = 2

    def __init__(self):
        displayio.release_displays()
        i2c = board.I2C()
        display_bus = I2CDisplayBus(i2c, device_address=0x3C)
        display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=self.display_width, height=self.display_height)
        self._splash = displayio.Group()
        display.root_group = self._splash
        self.button_press_counter = 0
        self.write_top_banner(f'!!Bonjour!!')

    def erase_top_banner(self):
        """
        Erase the top banner

        :return:
        """
        self._erase(self.display_width, self.top_banner_height)

    def erase_all(self):
        """
        Erase the top banner

        :return:
        """
        self._erase(self.display_width, self.display_height)

    def _erase(self, width, height, x_offset=0, y_offset=0):
        inner_bitmap = displayio.Bitmap(width, height, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = PIXEL_NO_FILL
        inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=x_offset, y=y_offset)
        self._splash.append(inner_sprite)

    def erase_main(self):
        self._erase(self.display_width, self.main_window_height, y_offset=self.main_window_top - 3)

    def erase_top_banner_message(self):
        self._erase(self.top_message_end_x, self.top_banner_height)

    def draw_battery(self, charge):
        self._erase(self.display_width - self.bat_main_rect_start_x, self.top_banner_height, x_offset=self.bat_main_rect_start_x)
        outer_outline = Polygon([
            (self.bat_main_rect_start_x, self.bat_main_rect_start_y),
            (self.bat_main_rect_end_x, self.bat_main_rect_start_y),
            (self.bat_main_rect_end_x, self.bat_tip_start_y),
            (self.bat_main_rect_end_x + self.bat_tip_length, self.bat_tip_start_y),
            (self.bat_main_rect_end_x + self.bat_tip_length, self.bat_tip_end_y),
            (self.bat_main_rect_end_x, self.bat_tip_end_y),
            (self.bat_main_rect_end_x, self.bat_main_rect_end_y),
            (self.bat_main_rect_start_x, self.bat_main_rect_end_y),
        ], outline=PIXEL_FILL, colors=1)
        self._splash.append(outer_outline)
        fill_width = round(
            int((charge / 100) * (self.bat_main_rect_end_x - self.bat_main_rect_start_x)) / 4
        ) * 4
        print(f'fill_width: {fill_width}')
        if fill_width > 0:
            battery_fill = Rect(
                x=self.bat_main_rect_start_x,
                y=self.bat_main_rect_start_y,
                height=self.bat_main_rect_end_y - self.bat_main_rect_start_y,
                width=fill_width,
                fill=PIXEL_FILL,
                outline=PIXEL_FILL
            )
            self._splash.append(battery_fill)
            if charge >= 95:
                tip_fill = Rect(
                    x=self.bat_main_rect_end_x - 2,
                    y=self.bat_tip_start_y,
                    height=self.bat_tip_end_y - self.bat_tip_start_y,
                    width=self.bat_tip_length + 2,
                    fill=PIXEL_FILL,
                    outline=PIXEL_FILL
                )
                self._splash.append(tip_fill)

    def write_top_banner(self, message):
        """
        Write a message on the top banner

        :param message:
        :return:
        """
        self.erase_top_banner_message()
        text_area = label.Label(terminalio.FONT, text=message, color=PIXEL_FILL, x=2, y=3)
        self._splash.append(text_area)

    def write_main(self, message):
        self.erase_main()
        text_area = label.Label(terminalio.FONT, text=message, color=PIXEL_FILL, x=2, y=self.main_window_top)
        self._splash.append(text_area)
