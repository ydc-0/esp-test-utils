from typing import Any
from typing import AnyStr
from typing import Dict
from typing import Union

from ..base_port import PortWrapper


class DutMac(dict):
    @property
    def base(self) -> str:
        return self['base']  # type: ignore


class DutBaseWrapper(PortWrapper):
    """Add more dut related methods to"""

    def __init__(self, dut: Any, name: str, log_file: str = '') -> None:
        super().__init__(dut, name, log_file)
        # extra attributes
        self._mac = DutMac()

    def write_line(self, data: AnyStr, end: str = '\r\n') -> None:
        """Use \\r\\n as default ending"""
        return super().write_line(data, end)

    # Dut specific
    @property
    def mac(self) -> DutMac:
        return self._mac

    def stop_receive_thread(self) -> None:
        raise NotImplementedError()

    def start_receive_thread(self) -> None:
        self.start_pexpect_proc()

    # Attributes needed by bin path
    @property
    def bin_path(self) -> str:
        raise NotImplementedError()

    @property
    def sdkconfig(self) -> Dict[str, Any]:
        raise NotImplementedError()

    @property
    def target(self) -> str:
        raise NotImplementedError()

    @property
    def partition_table(self) -> Dict[str, Any]:
        raise NotImplementedError()

    # Serial Specific
    def reconfigure(self) -> bool:
        raise NotImplementedError()

    def hard_reset(self) -> None:
        raise NotImplementedError()

    # EspTool Specific
    def flash(self, bin_path: str = '') -> None:
        raise NotImplementedError()

    def flash_partition(self, part: Union[int, str], bin_path: str = '') -> None:
        raise NotImplementedError()

    def flash_nvs(self, bin_path: str = '') -> None:
        raise NotImplementedError()

    def dump_flash(self, part: Union[int, str], bin_path: str, size: int = 0) -> None:
        raise NotImplementedError()

    # More extra methods may be implemented
