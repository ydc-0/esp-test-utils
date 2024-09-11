# from esp_test_utils.config import EnvConfig
from serial import Serial

from esp_test_utils import dut_wrapper
from esp_test_utils.adapter.dut import DutBaseWrapper
from esp_test_utils.esp_console import ConsoleMixin


class JapDut(ConsoleMixin, DutBaseWrapper):  # noqa: W0223
    pass


def jap_test() -> None:
    ser = Serial('/dev/ttyUSB0', 115200, timeout=0.01)
    with dut_wrapper(ser, 'JAP', wrap_cls=JapDut) as dut:
        # dut.connect_to_ap()
        # TODO
        dut.write_line('help')


if __name__ == '__main__':
    jap_test()
