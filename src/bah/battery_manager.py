import re
import subprocess
from bah.display_controller import DisplayController

class BatteryManager:
    def __init__(self, display_controller: DisplayController):
        self._display_controller = display_controller
        self._current_battery_charge = 0
        self._get_battery_charge()

    def _get_battery_charge(self):
        result = subprocess.run(
            ['nc', '-q', '0', '-U', '/tmp/pisugar-server.sock'],
            input="get battery",
            text=True,  # Handle input/output as strings instead of bytes
            capture_output=True  # Capture stdout and stderr
        )
        match = re.match(r'^battery:\s*([0-9]+)', result.stdout)
        self._current_battery_charge = int(match.group(1))
