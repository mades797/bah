"""
BAH battery charge management module
"""
import logging
import re
import subprocess
from bah.display_controller import DisplayController
from bah.task_scheduler import TaskScheduler, Task

from bah.exceptions import BAHException

logger = logging.getLogger('bah-battery-manager')
logger.setLevel(logging.WARN)


class BatteryManager(TaskScheduler):
    """
    Class implementing battery charge management and reporting
    """

    def __init__(self, display_controller: DisplayController):
        super().__init__()
        self._display_controller = display_controller
        self._current_battery_charge = 0
        self._tasks = [
            Task(
                'get-battery-charge',
                15,
                self._get_battery_charge,
                self.set_battery_charge,
                on_exception=self.set_unknown
            ),
            Task(
                'get-battery-charging',
                5,
                self._get_battery_charging,
                self.set_battery_charging
            )
        ]

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    @staticmethod
    def _get_battery_charge() -> int:
        logger.info('Getting battery charge')
        result = subprocess.run(
            ['nc', '-q', '0', '-U', '/tmp/pisugar-server.sock'],
            input='get battery',
            text=True,
            capture_output=True,
            check=True,
        )
        match = re.match(r'^battery:\s*([0-9]+)', result.stdout)
        if match:
            return int(match.group(1))
        # TODO: handle error
        raise BAHException('Could not get battery charge')

    @staticmethod
    def _get_battery_charging() -> bool:
        logger.info('Getting battery charging')
        result = subprocess.run(
            ['nc', '-q', '0', '-U', '/tmp/pisugar-server.sock'],
            input='get battery_power_plugged',
            text=True,
            capture_output=True,
            check=True,
        )
        match = re.match(r'^battery_power_plugged:\s*(true|false)', result.stdout)
        if match:
            logger.debug('Battery charging: %s', match.group(1).lower() == 'true')
            return match.group(1).lower() == 'true'
            # return True
        # TODO: handle error
        raise BAHException(f'Could not get battery charge. Could not parse "{result.stdout}"')

    def set_battery_charge(self, battery_charge: int) -> None:
        """
        Set the battery charge percentage

        :param battery_charge: Percentage of battery charge [0-100]
        :return:
        """
        logger.info('Setting battery charge to: %d', battery_charge)
        self._current_battery_charge = battery_charge
        self._display_controller.battery_charge = battery_charge
        if not self._display_controller.is_battery_flashing():
            self._display_controller.draw_battery()

    def set_battery_charging(self, charging: bool) -> None:
        """
        Set the battery charge percentage

        :param charging: Flag to indicate that the battery is charging
        :return:
        """
        logger.debug('Setting battery charging to: %d', charging)
        self._display_controller.set_battery_charging(charging)

    def set_unknown(self, _error: BAHException) -> None:
        """
        Set the battery unknown symbol

        :param _error:
        :return:
        """
        logger.info('Setting battery charge to: unknown')
        self._display_controller.draw_battery_unknown()
