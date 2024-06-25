import abc
import functools
import re
import time
from typing import Any
from typing import AnyStr
from typing import Callable
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

import pexpect
import serial

from esp_test_utils.devices import SerialDut


class BaseDut(metaclass=abc.ABCMeta):
    """Define a minimum Dut class, the dut objects should at least support these methods

    the dut should at least support these methods:
    - write() with parameters: data[str]
    - expect() with parameters: pattern[str or re.Pattern], timeout[int] (seconds)
    """

    @classmethod
    def __subclasshook__(cls, subclass: object) -> bool:
        return (
            hasattr(subclass, 'write')
            and callable(subclass.write)
            and hasattr(subclass, 'expect')
            and callable(subclass.expect)
        )

    def write(self, data: AnyStr) -> None:
        """write string"""
        raise NotImplementedError('Dut class should implement this method')

    def expect(self, pattern: Union[str, bytes, re.Pattern], **kwargs: Any) -> Optional[re.Match]:
        """For dut classes from other test frameworks, must support input pattern types re.Pattern and str"""
        raise NotImplementedError('Dut class should implement this method')


class ExpectTimeout(TimeoutError):
    """raise same ExpectTimeout rather than different Exception from different framework"""


class DutWrapper:
    """Wrapper the dut class, to make it the same for all test methods in this package."""

    EXPECT_TIMEOUT_EXCEPTIONS: Tuple[Type[Exception], ...] = (Exception,)

    def __init__(self, dut: Any, name: Optional[str] = None) -> None:
        self._dut = dut
        self._name = name
        self.expect_timeout_exceptions = self.EXPECT_TIMEOUT_EXCEPTIONS

    @property
    def name(self) -> str:
        _name = self.name
        if not self._name and hasattr(self._dut, 'name'):
            _name = self._dut.name
        return _name

    @staticmethod
    def _handle_expect_timeout(func: Callable) -> Callable:
        """Raise same type exception ExpectTimeout for duts from different frameworks"""

        @functools.wraps(func)
        def wrap(self, *args, **kwargs):  # type: ignore
            try:
                result = func(self, *args, **kwargs)
            except self.expect_timeout_exceptions as e:
                raise ExpectTimeout(str(e)) from e
            return result

        return wrap

    def write(self, data: AnyStr) -> None:
        if not isinstance(self._dut, (BaseDut, SerialDut)):
            raise NotImplementedError()
        return self._dut.write(data)

    @_handle_expect_timeout
    def expect(self, pattern: Union[str, bytes, re.Pattern], timeout: Union[int, float] = 30) -> Optional[re.Match]:
        if not isinstance(self._dut, (BaseDut, SerialDut)):
            raise NotImplementedError()
        if isinstance(timeout, float):
            # Delay for a while if the timeout is float, pexpect only accept int values.
            time.sleep(0.001)
        return self._dut.expect(pattern, timeout=int(timeout))

    def read_all_data(self) -> bytes:
        """Read out all data from dut, return immediately.

        Returns:
            bytes: all data read from dut
        """
        try:
            match = self.expect(re.compile(b'.+', re.DOTALL), timeout=0)
            assert match
            data = match.group(0)
            assert isinstance(data, bytes)
            return data
        except ExpectTimeout:
            return b''

    def __enter__(self) -> 'DutWrapper':
        return self

    def __exit__(self, exc_type, exc_value, trace) -> None:  # type: ignore
        """Always close the dut serial and clean resources before exiting."""
        if hasattr(self._dut, 'close'):
            self._dut.close()


class SerialDutWrapper(DutWrapper):
    EXPECT_TIMEOUT_EXCEPTIONS = (pexpect.exceptions.TIMEOUT, TimeoutError)


class PytestDutWrapper(DutWrapper):
    # TBD
    pass


class ATSDutWrapper(DutWrapper):
    # TBD
    pass


def dut_wrapper(
    dut: Any,
    name: Optional[str] = None,
) -> DutWrapper:
    """wrap the dut from other frameworks.

    Supported dut types:
    - pytest-embedded dut
    - tiny-test-fw dut
    - ATS UartPort
    - SerialDut
    - serial.Serial: will be converted to SerialDut, please do not read
    - Other dut objects that matched ``BaseDut``.

    Args:
        dut (Any): the dut object from other frameworks
        name (str, optional): set name for dut wrapper, not supported getting from dut class by default.

    Returns:
        DutWrapper: _description_
    """
    if isinstance(dut, SerialDut):
        return SerialDutWrapper(dut, name)
    if isinstance(dut, serial.Serial):
        if not name:
            name = dut.port
        assert name
        ser_dut = SerialDut(name, port=None)
        ser_dut.serial = dut
        return SerialDutWrapper(ser_dut)
    try:
        from pytest_embedded import Dut

        if isinstance(dut, Dut):
            raise NotImplementedError('pytest_embedded Dut is not supported yet.')
    except ImportError:
        # pytest-embedded is not a required package.
        # ignore import error.
        pass
    if isinstance(dut, BaseDut):
        return DutWrapper(dut, name)
    raise NotImplementedError(f'Not supported dut type: {type(dut)}')
