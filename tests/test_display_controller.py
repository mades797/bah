# pylint: disable=W0212 (protected-access), R0904 (too-many-public-methods), R0903 (too-few-public-methods)
"""
Test module for DisplayController
"""
import time
from unittest import mock

import terminalio
import pytest

from bah.display_controller import DisplayController, DisplayControllerException


@pytest.fixture(name='display_controller')
def fixture_display_controller() -> DisplayController:
    """
    Fixture to create a DisplayController instance with the actual interface to the display mocked

    :return: DisplayController instance
    """
    with (
        mock.patch('bah.display_controller.displayio'),
        mock.patch('bah.display_controller.I2CDisplayBus'),
        mock.patch('bah.display_controller.adafruit_displayio_ssd1306'),
    ):
        return DisplayController()


class TestDisplayController:
    """
    Test class for DisplayController class
    """

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController._erase')
    def test_erase_top_banner(mock_erase, display_controller):
        """
        Test `erase_top_banner` method

        Expected result: The `_erase` method is called with the right arguments
        """
        display_controller.erase_top_banner()
        mock_erase.assert_called_once_with(DisplayController.display_width, DisplayController.top_banner_height)

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController._erase')
    def test_erase_all(mock_erase, display_controller):
        """
        Test `erase_all` method

        Expected result: The `_erase` method is called with the right arguments
        """
        display_controller.erase_all()
        mock_erase.assert_called_once_with(DisplayController.display_width, DisplayController.display_height)

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_init_error(mock_displayio) -> None:
        """
        Test the constructor when an error occurs

        Expected result: The constructor raises a DisplayControllerException with the correct error message
        """
        mock_displayio.release_displays.side_effect = IOError('this is an IOError')
        DisplayController._instance = None
        with pytest.raises(DisplayControllerException):
            try:
                DisplayController()
            except DisplayControllerException as error:
                assert str(error) == 'Failed to initialize display controller'
                raise error

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_download_indicator')
    @mock.patch('bah.display_controller.DisplayController.draw_download_indicator')
    def test_download_flash(mock_draw_download_indicator, mock_erase_download_indicator, display_controller) -> None:
        """
        Test the download indicator flashing

        Expected result: The `draw_download_indicator` and `erase_download_indicator` methods are called to produce
        the flashing
        """
        display_controller.start_download_flash()
        time.sleep(2)
        display_controller.stop_download_flash()
        mock_draw_download_indicator.assert_called()
        mock_erase_download_indicator.assert_called()
        assert not display_controller._download_flash_thread.is_alive()

    @staticmethod
    def test_download_flash_stop_redundant(display_controller) -> None:
        """
        This test validates a redundant call to `stop_download_flash` as the object's thread is None

        Expected result: The download_flash thread is not joined
        """
        display_controller._download_flash_stop = mock.MagicMock()
        display_controller._download_flash_thread = None
        display_controller.stop_download_flash()
        display_controller._download_flash_stop.assert_not_called()

    @staticmethod
    def test_download_flash_stop_redundant_2(display_controller) -> None:
        """
        This test validates a redundant call to `stop_download_flash` as the object's stop event is None

        Expected result: The download_flash thread is not joined
        """
        display_controller._download_flash_thread = mock.MagicMock()
        display_controller._download_flash_stop = None
        display_controller.stop_download_flash()
        display_controller._download_flash_thread.assert_not_called()

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_erase_battery(mock_displayio, display_controller) -> None:
        """
        Test `erase_battery` method

        Expected result: A bitmap is created with the right coordinates and written on the display
        """
        display_controller.erase_battery()
        mock_displayio.Bitmap.assert_called_once_with(20, 11, 1)
        mock_displayio.Palette.assert_called_once_with(1)
        mock_displayio.Palette.return_value.__setitem__.assert_has_calls([mock.call(0, 0)])
        mock_displayio.TileGrid.assert_called_once_with(
            mock_displayio.Bitmap.return_value,
            pixel_shader=mock_displayio.Palette.return_value,
            x=108,
            y=0
        )
        display_controller._splash.assert_has_calls([mock.call.append(mock_displayio.TileGrid.return_value)])

    @staticmethod
    @mock.patch('bah.display_controller.Rect')
    @mock.patch('bah.display_controller.Line')
    def test_erase_network(mock_line, mock_rect, display_controller) -> None:
        """
        Test `erase_network` method

        The right bitmap is created to erase the network indicator
        """
        display_controller.erase_network()
        # Network indicator written with no-fill to erase the symbol
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_rect.return_value),
            mock.call(mock_rect.return_value),
            mock.call(mock_rect.return_value),
            mock.call(mock_rect.return_value),
            mock.call(mock_line.return_value),
            mock.call(mock_line.return_value),
        ], any_order=True)

        mock_rect.assert_has_calls([
            mock.call(90, 8, 4, 4, fill=0, outline=0),
            mock.call(94, 6, 4, 6, fill=0, outline=0),
            mock.call(98, 4, 4, 8, fill=0, outline=0),
            mock.call(102, 2, 4, 10, fill=0, outline=0)
        ], any_order=True)
        mock_line.assert_has_calls([
            mock.call(90, 2, 106, 12, color=0),
            mock.call(90, 3, 106, 13, color=0)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_erase_main(mock_displayio, display_controller) -> None:
        """
        Test `erase_main` method

        Expected result: The right bitmap is created to erase the entire main window
        """
        display_controller._splash.reset_mock()
        display_controller.erase_main()
        mock_displayio.Bitmap.assert_called_once_with(128, 48, 1)
        mock_displayio.Palette.assert_called_once_with(1)
        mock_displayio.Palette.return_value.__setitem__.assert_called_once_with(0, 0)
        mock_displayio.TileGrid.assert_called_once_with(
            mock_displayio.Bitmap.return_value,
            pixel_shader=mock_displayio.Palette.return_value,
            x=0,
            y=18
        )
        display_controller._splash.append.assert_called_once_with(mock_displayio.TileGrid.return_value)

    @staticmethod
    @mock.patch('bah.display_controller.displayio')
    def test_erase_download_indicator(mock_displayio, display_controller) -> None:
        """
        Test `erase_download_indicator` method

        Expected result: The right bitmap is created to erase the download indicator
        """
        display_controller._splash.reset_mock()
        display_controller.erase_download_indicator()
        mock_displayio.Bitmap.assert_called_once_with(10, 12, 1)
        mock_displayio.Palette.assert_called_once_with(1)
        mock_displayio.Palette.return_value.__setitem__.assert_called_once_with(0, 0)
        mock_displayio.TileGrid.assert_called_once_with(
            mock_displayio.Bitmap.return_value,
            pixel_shader=mock_displayio.Palette.return_value,
            x=74,
            y=0
        )
        display_controller._splash.append.assert_called_once_with(mock_displayio.TileGrid.return_value)

    @staticmethod
    @mock.patch('bah.display_controller.FilledPolygon')
    def test_draw_download_indicator(mock_filled_polygon, display_controller) -> None:
        """
        Test `draw_download_indicator` method

        Expected result: The right FilledPolygon is created to draw the download indicator
        """
        display_controller._splash.reset_mock()
        display_controller.draw_download_indicator()
        display_controller._splash.append.assert_called_once_with(mock_filled_polygon.return_value)
        mock_filled_polygon.assert_called_once_with([
            (77, 2),
            (77, 6),
            (75, 6),
            (79, 10),
            (83, 6),
            (81, 6),
            (81, 2),
        ], outline=0xFFFFFF, fill=0xFFFFFF)

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_25(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 25%

        Expected result: The battery symbol is drawn with the right battery fill
        """
        display_controller._splash.reset_mock()
        display_controller.battery_charge = 28
        display_controller.draw_battery()
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_called_once_with(x=108, y=2, height=8, width=4, fill=0xFFFFFF, outline=0xFFFFFF)
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_35(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 35%

        Expected result: The battery symbol is drawn with the right battery fill
        """
        display_controller._splash.reset_mock()
        display_controller.battery_charge = 35
        display_controller.draw_battery()
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_called_once_with(x=108, y=2, height=8, width=8, fill=0xFFFFFF, outline=0xFFFFFF)
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_65(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 65%

        Expected result: The battery symbol is drawn with the right battery fill
        """
        display_controller._splash.reset_mock()
        display_controller.battery_charge = 65
        display_controller.draw_battery()
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_called_once_with(x=108, y=2, height=8, width=12, fill=0xFFFFFF, outline=0xFFFFFF)
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_75(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 75%

        Expected result: The battery symbol is drawn with the right battery fill
        """
        display_controller._splash.reset_mock()
        display_controller.battery_charge = 78
        display_controller.draw_battery()
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_called_once_with(x=108, y=2, height=8, width=16, fill=0xFFFFFF, outline=0xFFFFFF)
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_98(mock_rect, mock_polygon, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 98%

        Expected result: The battery symbol is drawn with the right battery fill and the battery tip
        """
        display_controller._splash.reset_mock()
        display_controller.battery_charge = 98
        display_controller.draw_battery()
        mock_erase_battery.assert_called_once()
        mock_polygon.assert_called_once_with([
            (108, 2),
            (124, 2),
            (124, 4),
            (126, 4),
            (126, 8),
            (124, 8),
            (124, 10),
            (108, 10),
        ], outline=0xFFFFFF, colors=1)
        mock_rect.assert_has_calls([
            mock.call(x=108, y=2, height=8, width=16, fill=0xFFFFFF, outline=0xFFFFFF),
            mock.call(x=122, y=4, height=4, width=4, fill=0xFFFFFF, outline=0xFFFFFF),
        ])
        display_controller._splash.append.assert_has_calls([
            mock.call(mock_polygon.return_value),
            mock.call(mock_rect.return_value)
        ])

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController._erase')
    @mock.patch('bah.display_controller.Polygon')
    @mock.patch('bah.display_controller.Rect')
    def test_draw_battery_1(_mock_rect, _mock_polygon, _mock_erase, display_controller) -> None:
        """
        Test the `draw_battery` method` with a charge of 1%

        Expected result: The battery symbol is drawn
        """
        # TODO
        display_controller._splash.reset_mock()
        display_controller.battery_charge = 1
        display_controller.draw_battery()

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    @mock.patch('bah.display_controller.label')
    def test_draw_battery_unknown(mock_label, mock_erase_battery, display_controller) -> None:
        """
        Test the `draw_battery_unknown` method

        Expected result: The "battery unknown" symbol is drawn
        """
        display_controller._splash.reset_mock()
        display_controller.draw_battery_unknown()
        mock_erase_battery.assert_called_once()
        mock_label.Label.assert_called_once_with(terminalio.FONT, text='???', color=0xFFFFFF, x=108, y=4)
        display_controller._splash.append.assert_called_once_with(mock_label.Label.return_value)

    @staticmethod
    def test_is_battery_flashing_false(display_controller) -> None:
        """
        Test the `is_battery_flashing` method when the battery indicator is not flashing

        Expected result: The method returns False
        """
        display_controller._battery_flash_thread = mock.MagicMock()
        display_controller._battery_flash_thread.is_alive.return_value = False
        assert not display_controller.is_battery_flashing()

    @staticmethod
    def test_is_battery_flashing_true(display_controller) -> None:
        """
        Test the `is_battery_flashing` method when the battery indicator is flashing

        Expected result: The method returns True
        """
        display_controller._battery_flash_thread = mock.MagicMock()
        display_controller._battery_flash_thread.is_alive.return_value = True
        assert display_controller.is_battery_flashing()

    @staticmethod
    def test_set_battery_charging_2_charging(display_controller) -> None:
        """
        Test the `set_battery_charging` method when the battery is not charging and transitions to charging

        Expected result: The battery indicator should start flashing
        """
        with (mock.patch('bah.display_controller.DisplayController.start_battery_flash') as mock_start_battery_flash,
              mock.patch('bah.display_controller.DisplayController.stop_battery_flash') as mock_stop_battery_flash,
              mock.patch('bah.display_controller.DisplayController.is_battery_flashing', return_value=False)):
            display_controller.set_battery_charging(True)
            mock_start_battery_flash.assert_called_once()
            mock_stop_battery_flash.assert_not_called()

    @staticmethod
    def test_set_battery_charging_2_not_charging(display_controller) -> None:
        """
        Test the `set_battery_charging` method when the battery is charging and transitions to not charging

        Expected result: The battery indicator should stop flashing
        """
        with (mock.patch('bah.display_controller.DisplayController.start_battery_flash') as mock_start_battery_flash,
              mock.patch('bah.display_controller.DisplayController.stop_battery_flash') as mock_stop_battery_flash,
              mock.patch('bah.display_controller.DisplayController.is_battery_flashing', return_value=True)):
            display_controller.set_battery_charging(False)
            mock_start_battery_flash.assert_not_called()
            mock_stop_battery_flash.assert_called_once()

    @staticmethod
    def test_set_battery_charging_already_charging(display_controller) -> None:
        """
        Test the `set_battery_charging` method when the battery is set to charging but was already flashing

        Expected result: Nothing is done
        """
        with (mock.patch('bah.display_controller.DisplayController.start_battery_flash') as mock_start_battery_flash,
              mock.patch('bah.display_controller.DisplayController.stop_battery_flash') as mock_stop_battery_flash,
              mock.patch('bah.display_controller.DisplayController.is_battery_flashing', return_value=True)):
            display_controller.set_battery_charging(True)
            mock_start_battery_flash.assert_not_called()
            mock_stop_battery_flash.assert_not_called()

    @staticmethod
    def test_set_battery_charging_already_not_charging(display_controller) -> None:
        """
        Test the `set_battery_charging` method when the battery is set to not charging but was already not flashing

        Expected result: Nothing is done
        """
        with (mock.patch('bah.display_controller.DisplayController.start_battery_flash') as mock_start_battery_flash,
              mock.patch('bah.display_controller.DisplayController.stop_battery_flash') as mock_stop_battery_flash,
              mock.patch('bah.display_controller.DisplayController.is_battery_flashing', return_value=False)):
            display_controller.set_battery_charging(False)
            mock_start_battery_flash.assert_not_called()
            mock_stop_battery_flash.assert_not_called()

    @staticmethod
    @mock.patch('bah.display_controller.DisplayController.draw_battery')
    @mock.patch('bah.display_controller.DisplayController.erase_battery')
    def test_battery_flash(mock_draw_battery, mock_erase_battery, display_controller) -> None:
        """
        Test the battery flashing

        Expected result: The `draw_battery` and `erase_battery` methods are called to produce
        the flashing
        """
        display_controller.start_battery_flash()
        time.sleep(2)
        display_controller.stop_battery_flash()
        mock_draw_battery.assert_called()
        mock_erase_battery.assert_called()
        assert not display_controller._battery_flash_thread.is_alive()

    @staticmethod
    def test_battery_flash_stop_redundant(display_controller) -> None:
        """
        This test validates a redundant call to `stop_battery_flash` as the object's thread is None

        Expected result: The _battery_flash_thread thread is not joined
        """
        display_controller._battery_flash_stop = mock.MagicMock()
        display_controller._battery_flash_thread = None
        display_controller.stop_battery_flash()
        display_controller._battery_flash_stop.assert_not_called()

    @staticmethod
    def test_battery_flash_stop_redundant_2(display_controller) -> None:
        """
        This test validates a redundant call to `stop_battery_flash` as the object's stop event is None

        Expected result: The _battery_flash_thread thread is not joined
        """
        display_controller._battery_flash_thread = mock.MagicMock()
        display_controller._battery_flash_stop = None
        display_controller.stop_battery_flash()
        display_controller._battery_flash_thread.assert_not_called()
