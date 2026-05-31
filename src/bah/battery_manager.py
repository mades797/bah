"""
BAH battery charge management module
"""
import logging
import re
import subprocess
from bah.display_controller import DisplayController
from bah.task_scheduler import TaskScheduler, Task

from bah.exceptions import BAHException


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
                5,
                self._get_battery_charge,
                self.set_battery_charge,
                on_exception=self.set_unknown
            )
        ]

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    @staticmethod
    def _get_battery_charge() -> int:
        logging.info('Getting battery charge')
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

    def set_battery_charge(self, battery_charge: int) -> None:
        """
        Set the battery charge percentage

        :param battery_charge: Percentage of battery charge [0-100]
        :return:
        """
        logging.info('Setting battery charge to: %d', battery_charge)
        self._current_battery_charge = battery_charge
        self._display_controller.draw_battery(battery_charge)

    def set_unknown(self, _error: BAHException) -> None:
        """
        Set the battery unknown symbol

        :param _error:
        :return:
        """
        logging.info('Setting battery charge to: unknown')
        self._display_controller.draw_battery_unknown()
