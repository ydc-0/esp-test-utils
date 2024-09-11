from typing import Any
from typing import List
from typing import Optional
from typing import Type

import serial

from ...devices import SerialDut
from ..base_port import BasePort
from .dut_base import DutBaseWrapper

# T = TypeVar('T', bound=DutBaseWrapper)


def dut_wrapper(
    dut: Any,
    name: str = '',
    log_file: str = '',
    wrap_cls: Type = DutBaseWrapper,
    extra_mixins: Optional[List[Type]] = None,
) -> DutBaseWrapper:
    """wrap the dut from other frameworks.

    Supported dut types:
    - SerialPort
    - serial.Serial: will be converted to ``SerialPort``
    - TBD: pytest-embedded dut
    - TBD: tiny-test-fw dut
    - TBD: ATS UartPort
    - Other objects that matched ``BasePort``.

    Args:
        dut (Any): the dut object from other frameworks
        name (str, optional): set name for dut wrapper, not supported getting from dut class by default.
        log_file (str, optional): set name for dut wrapper, not supported getting from dut class by default.
        pexpect_timeout (float, optional): default pexpect timeout
        extra_mixins (List[Type], optional): Extra mixin classes for DutBaseWrapper

    Returns:
        DutBaseWrapper: dut object
    """
    assert issubclass(wrap_cls, DutBaseWrapper)
    mixins = extra_mixins if extra_mixins else []

    wrap_dut: Optional[DutBaseWrapper] = None

    if isinstance(dut, SerialDut):
        wrap_dut = dut
        if name and name != wrap_dut.name:
            wrap_dut.name = name
        if log_file and log_file != wrap_dut.log_file:
            wrap_dut.log_file = log_file
    elif isinstance(dut, serial.Serial):
        wrap_dut = SerialDut(dut, name, log_file)
    elif isinstance(dut, BasePort):
        wrap_dut = DutBaseWrapper(dut, name, log_file)
    else:
        raise NotImplementedError(f'Not supported dut type: {type(dut)}')

    class NewClass(*mixins, wrap_dut.__class__):  # type: ignore
        pass

    wrap_dut.__class__ = NewClass
    return wrap_dut  # type: ignore
