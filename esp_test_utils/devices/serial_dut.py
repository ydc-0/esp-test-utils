from typing import TYPE_CHECKING
from typing import TypeAlias

from serial import Serial

from ..adapter.dut.dut_base import DutBaseWrapper
from ..adapter.dut.serial_dut import SerialDutMixin
from ..logger import get_logger


if TYPE_CHECKING:
    MixinBase: TypeAlias = 'DutBaseWrapper'
else:
    MixinBase = object

logger = get_logger('SerialDut')


class SerialDut(SerialDutMixin, DutBaseWrapper):
    """A basic Dut class that supports serial port read and write

    This class using serial with pexpect.
    """

    def __init__(self, dut: Serial, name: str, log_file: str = '') -> None:
        if not dut:
            self.INIT_START_PEXPECT_PROC = False  # pylint: disable=invalid-name
        super().__init__(dut, name, log_file)
