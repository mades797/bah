"""
DisplayController module
"""
import threading
import time

import adafruit_displayio_ssd1306
from adafruit_display_text import label
import board
import displayio
from i2cdisplaybus import I2CDisplayBus
import terminalio
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.polygon import Polygon
from adafruit_display_shapes.filled_polygon import FilledPolygon

from bah.exceptions import BAHException


PIXEL_FILL = 0xFFFFFF
PIXEL_NO_FILL = 0x0
BAT_UNKNOWN_TEXT = '???'


class DisplayControllerException(BAHException):
    """
    DisplayController exception
    """


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

    # Download indicator (down arrow)
    download_indicator_start_x = 75
    download_indicator_end_x = 83
    download_indicator_start_y = 2
    download_indicator_end_y = 10

    # Network indication
    network_indication_start_x = 90
    network_bar_width = 4
    network_bar_1_height = 4
    network_bar_2_height = 6
    network_bar_3_height = 8
    network_bar_4_height = 10
    network_indication_start_y = 2
    network_indication_end_y = 12

    network_indication_end_x = 106

    # Battery charge indication
    bat_main_rect_start_x = 108
    bat_main_rect_end_x = 124
    bat_main_rect_start_y = 2
    bat_main_rect_end_y = 10
    bat_tip_start_y = 4
    bat_tip_end_y = 8
    bat_tip_length = 2

    # Singleton
    _instance = None

    def __new__(cls) -> 'DisplayController':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        try:
            displayio.release_displays()
            i2c = board.I2C()
            display_bus = I2CDisplayBus(i2c, device_address=0x3C)
            display = adafruit_displayio_ssd1306.SSD1306(
                display_bus,
                width=self.display_width,
                height=self.display_height
            )
            self._splash = displayio.Group()
            display.root_group = self._splash
            self._download_flash_thread: threading.Thread | None = None
            self._download_flash_stop: threading.Event | None = None
            self.write_top_banner('!!Bonjour!!')
        except Exception as error:
            raise DisplayControllerException('Failed to initialize display controller') from error

    def _download_flash(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            self.draw_download_indicator()
            time.sleep(0.5)
            self.erase_download_indicator()
            time.sleep(0.5)
        self.erase_download_indicator()

    def start_download_flash(self) -> None:
        """
        Start the flashing of the "download" indicator

        :return:
        """
        self._download_flash_stop = threading.Event()
        self._download_flash_thread = threading.Thread(target=self._download_flash, args=(self._download_flash_stop,))
        self._download_flash_thread.start()

    def stop_download_flash(self) -> None:
        """
        Stop the flashing of the "downloading" indicator

        :return:
        """
        if self._download_flash_thread is not None and self._download_flash_stop is not None:
            self._download_flash_stop.set()
            self._download_flash_thread.join()

    def erase_top_banner(self) -> None:
        """
        Erase the top banner

        :return:
        """
        self._erase(self.display_width, self.top_banner_height)

    def erase_all(self) -> None:
        """
        Erase the top banner

        :return:
        """
        self._erase(self.display_width, self.display_height)

    def _erase(self, width: int, height: int, x_offset: int = 0, y_offset: int = 0) -> None:
        inner_bitmap = displayio.Bitmap(width, height, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = PIXEL_NO_FILL
        inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=x_offset, y=y_offset)
        self._splash.append(inner_sprite)

    def erase_battery(self) -> None:
        """
        Erase the battery indicator

        :return:
        """
        self._erase(
            self.display_width - self.bat_main_rect_start_x,
            self.bat_main_rect_end_y + 1,
            self.bat_main_rect_start_x
        )

    def erase_network(self) -> None:
        """
        Erase the network indicator

        :return:
        """
        self.draw_no_network(PIXEL_NO_FILL)

    def erase_main(self) -> None:
        """
        Erase the main screen

        :return:
        """
        self._erase(self.display_width, self.main_window_height, y_offset=self.main_window_top - 3)

    def erase_top_banner_message(self) -> None:
        """
        Erase the top banner message

        :return:
        """
        self._erase(self.top_message_end_x, self.top_banner_height)

    def draw_network(self, color: int = PIXEL_FILL) -> None:
        """
        Draw the "network" indication

        :param color: Color of the indication (fill or no fill)
        :return:
        """
        bar1 = Rect(
            self.network_indication_start_x,
            self.network_indication_end_y - self.network_bar_1_height,
            self.network_bar_width,
            self.network_bar_1_height,
            fill=color,
            outline=PIXEL_NO_FILL
        )
        bar2 = Rect(
            self.network_indication_start_x + self.network_bar_width,
            self.network_indication_end_y - self.network_bar_2_height,
            self.network_bar_width,
            self.network_bar_2_height,
            fill=color,
            outline=PIXEL_NO_FILL
        )
        bar3 = Rect(
            self.network_indication_start_x + (2 * self.network_bar_width),
            self.network_indication_end_y - self.network_bar_3_height,
            self.network_bar_width,
            self.network_bar_3_height,
            fill=color,
            outline=PIXEL_NO_FILL
        )
        bar4 = Rect(
            self.network_indication_start_x + (3 * self.network_bar_width),
            self.network_indication_end_y - self.network_bar_4_height,
            self.network_bar_width,
            self.network_bar_4_height,
            fill=color,
            outline=PIXEL_NO_FILL
        )
        self._splash.append(bar1)
        self._splash.append(bar2)
        self._splash.append(bar3)
        self._splash.append(bar4)

    def draw_no_network(self, color: int = PIXEL_FILL) -> None:
        """
        Draw the "no network" indication

        :param color: Color of the indication (fill or no fill)
        :return:
        """
        self.draw_network(color)
        line = Line(
            self.network_indication_start_x,
            self.network_indication_start_y,
            self.network_indication_end_x,
            self.network_indication_end_y,
            color=color
        )
        line2 = Line(
            self.network_indication_start_x,
            self.network_indication_start_y + 1,
            self.network_indication_end_x,
            self.network_indication_end_y + 1,
            color=color
        )
        self._splash.append(line)
        self._splash.append(line2)

    def erase_download_indicator(self) -> None:
        """
        Erase the "downloading" indicator

        :return:
        """
        self._erase(
            self.download_indicator_end_x - self.download_indicator_start_x + 2,
            self.download_indicator_end_y + 2,
            self.download_indicator_start_x - 1
        )

    def draw_download_indicator(self) -> None:
        """
        Draw the "downloading" indicator (arrow pointing down)

        :return:
        """
        shape = FilledPolygon([
                (self.download_indicator_start_x + 2, self.download_indicator_start_y),
                (self.download_indicator_start_x + 2, self.download_indicator_start_y + 4),
                (self.download_indicator_start_x, self.download_indicator_start_y + 4),
                (self.download_indicator_start_x + 4, self.download_indicator_end_y),
                (self.download_indicator_end_x, self.download_indicator_start_y + 4),
                (self.download_indicator_end_x - 2, self.download_indicator_start_y + 4),
                (self.download_indicator_end_x - 2, self.download_indicator_start_y)
            ],
            outline=PIXEL_FILL,
            fill=PIXEL_FILL
        )
        self._splash.append(shape)

    def draw_battery(self, charge: int) -> None:
        """
        Draw the battery charge symbol with the corresponding charge

        :param charge:
        :return:
        """
        self.erase_battery()
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
        if charge > 5:
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

    def draw_battery_unknown(self) -> None:
        """
        Draw the battery symbol with unknown charge

        :return:
        """
        self.erase_battery()
        text_area = label.Label(
            terminalio.FONT,
            text=BAT_UNKNOWN_TEXT,
            color=PIXEL_FILL,
            x=self.bat_main_rect_start_x,
            y=4
        )
        self._splash.append(text_area)

    def write_top_banner(self, message: str) -> None:
        """
        Write a message on the top banner

        :param message:
        :return:
        """
        self.erase_top_banner_message()
        text_area = label.Label(terminalio.FONT, text=message, color=PIXEL_FILL, x=2, y=3)
        self._splash.append(text_area)

    def write_main(self, message: str) -> None:
        """
        Write the message on the main screen

        :param message:
        :return:
        """
        self.erase_main()
        text_area = label.Label(terminalio.FONT, text=message, color=PIXEL_FILL, x=2, y=self.main_window_top)
        self._splash.append(text_area)
