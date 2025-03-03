from dataclasses import asdict
from dataclasses import dataclass
from itertools import product
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import TypeAlias
from typing import Union

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from ..logger import get_logger

VarType: TypeAlias = Union[int, float, str]
logger = get_logger('iperf-util')


@dataclass
class IperfResult:
    """One point iperf result, including type, att, rssi, max, avg, min, heap, etc."""

    avg: float
    max: float = -1  # Can be ignored
    min: float = -1  # Can be ignored
    throughput_list: Optional[List[float]] = None
    unit: str = 'Mbits/sec'
    min_heap: int = 0
    bandwidth: int = 0  # 20/40
    channel: int = 0
    rssi: float = -128
    type: str = 'iperf'  # tcp_tx, tcp_rx, udp_tx, udp_rx
    target: str = ''  # esp32, esp32s2, etc.
    errors: Optional[List[str]] = None
    # Advanced
    att: int = 0
    config_name: str = 'unknown'
    ap_name: str = 'unknown'
    version: str = 'unknown'

    def to_dict(self, with_keys: Optional[List[str]] = None) -> Dict[str, float]:
        """_summary_

        Args:
            with_keys (Optional[List[str]], optional): dict keys. default [avg,max,min,min_heap,rssi].
        """
        if not with_keys:
            with_keys = ['avg', 'max', 'min', 'min_heap', 'rssi']

        d = {}
        for k, v in asdict(self).items():
            if k not in with_keys:
                continue
            if not isinstance(v, (int, float)):
                logger.error(f'Variable of {k} must be a number, got {v}')
                raise ValueError(f'Variable of {k} must be a number, got {v}')
            d[k] = v
        return d


class IperfResultsRecord:
    """record, analysis iperf test results for different configs"""

    def __init__(self) -> None:
        self._results: List[IperfResult] = []
        self._aps: Set[str] = set()
        self._targets: Set[str] = set()
        self._types: Set[str] = set()

    def append_result(self, result: IperfResult) -> None:
        self._results.append(result)
        self._aps.add(result.ap_name)
        self._targets.add(result.target)
        self._types.add(result.type)

    def part(self, filter_fn: Callable[[IperfResult], bool]) -> 'Self':
        new_record = self.__class__()
        for result in self._results:
            if filter_fn(result):
                continue
            new_record.append_result(result)
        return new_record

    def _dict_by_key(
        self,
        key: str,
        filter_fn: Optional[Callable[[IperfResult], bool]] = None,
        reverse: bool = False,
    ) -> Dict[VarType, List[IperfResult]]:
        if not self._results:
            raise ValueError('No iperf test results recorded.')
        key_list = list(sorted({getattr(r, key) for r in self._results}, reverse=reverse))
        if len(key_list) <= 1:
            logger.info(f'Did not find different {key} in iperf test results.')
        d_key: Dict[VarType, List[IperfResult]] = {k: [] for k in key_list}
        for res in self._results:
            if filter_fn and not filter_fn(res):
                continue
            d_key[getattr(res, key)].append(res)
        return d_key

    def dict_by_att(
        self, filter_fn: Optional[Callable[[IperfResult], bool]] = None
    ) -> Dict[VarType, List[IperfResult]]:
        return self._dict_by_key('att', filter_fn)

    def dict_by_ap(self, filter_fn: Optional[Callable[[IperfResult], bool]] = None) -> Dict[VarType, List[IperfResult]]:
        return self._dict_by_key('ap_name', filter_fn)

    def _format_label_str(self, base_label: str, ap_name: str = '', target: str = '') -> str:
        assert base_label
        labels = []
        if len(self._aps) > 1:
            labels.append(ap_name)
        if len(self._targets) > 1:
            labels.append(target)
        labels.append(base_label)
        label_str = '_'.join(labels)
        return label_str

    @staticmethod
    def _get_matched_result(
        from_results: Iterable[IperfResult], filter_fn: Callable[[IperfResult], bool]
    ) -> Optional[IperfResult]:
        """Get first matched result by given condition"""
        for result in from_results:
            if filter_fn(result):
                return result
        return None

    def draw_rssi_vs_att_chart(
        self,
        file_name: str,
        title: str = 'RSSI vs ATT',
    ) -> None:
        # Needs extra packages to draw the chart
        from .line_chart import draw_line_chart_basic

        raw_data = self.dict_by_att()

        x_data: List[int] = []
        y_data: List[Dict[str, Optional[float]]] = []
        for att, results in raw_data.items():
            assert isinstance(att, int)
            x_data.append(att)
            _data: Dict[str, Optional[float]] = {}
            for ap, target in product(self._aps, self._targets):
                # pylint: disable=cell-var-from-loop
                label = self._format_label_str('rssi', ap, target)
                result = self._get_matched_result(results, lambda res: res.ap_name == ap and res.target == target)
                if result:
                    _data[label] = result.rssi
                else:
                    _data[label] = None
            y_data.append(_data)
        draw_line_chart_basic(file_name, title, y_data, x_data, x_label='att', y_label='rssi')

    def draw_rate_vs_rssi_chart(
        self,
        file_name: str,
        title: str = 'Rate vs RSSI',
        throughput_type: str = 'max',
    ) -> None:
        # Needs extra packages to draw the chart
        from .line_chart import draw_line_chart_basic

        # draw rssi chart from high rssi to low rssi
        raw_data = self._dict_by_key('rssi', reverse=True)

        x_data: List[float] = []
        y_data: List[Dict[str, Optional[float]]] = []
        for rssi, results in raw_data.items():
            assert isinstance(rssi, (int, float))
            x_data.append(-rssi)  # left value is higher rssi
            _data: Dict[str, Optional[float]] = {}
            for ap, target, typ in product(self._aps, self._targets, self._types):
                # pylint: disable=cell-var-from-loop
                label = self._format_label_str(typ, ap, target)
                result = self._get_matched_result(
                    results, filter_fn=lambda res: res.ap_name == ap and res.target == target and res.type == typ
                )
                if result:
                    _data[label] = result.avg if throughput_type == 'avg' else result.max
                else:
                    _data[label] = None
            y_data.append(_data)
        draw_line_chart_basic(file_name, title, y_data, x_data, x_label='rssi (-)', y_label='rate')
