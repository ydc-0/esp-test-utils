from dataclasses import asdict
from dataclasses import dataclass
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from ..logger import get_logger

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
    rssi: int = -128
    type: str = ''  # tcp_tx, tcp_rx, udp_tx, udp_rx
    target: str = ''  # esp32, esp32s2, etc.
    errors: Optional[List[str]] = None
    # Advanced
    att: int = 0
    config_name: str = 'unknown'
    ap_ssid: str = 'unknown'
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

    def append_result(self, result: IperfResult) -> None:
        self._results.append(result)

    def _dict_by_key(
        self, key: str, filter_fn: Optional[Callable[[IperfResult], bool]] = None
    ) -> Dict[int, List[IperfResult]]:
        if not self._results:
            raise ValueError('No iperf test results recorded.')
        key_list = list(sorted({getattr(r, key) for r in self._results}))
        if len(key_list) <= 1:
            logger.info(f'Did not find different {key} in iperf test results.')
        d_key = {k: [] for k in key_list}
        for res in self._results:
            if filter_fn and not filter_fn(res):
                continue
            d_key[getattr(res, key)].append(res)
        return d_key

    def dict_by_att(self, filter_fn: Optional[Callable[[IperfResult], bool]] = None) -> Dict[int, List[IperfResult]]:
        return self._dict_by_key('att', filter_fn)

    def dict_by_rssi(self, filter_fn: Optional[Callable[[IperfResult], bool]] = None) -> Dict[int, List[IperfResult]]:
        return self._dict_by_key('rssi', filter_fn)

    def dict_by_ap(self, filter_fn: Optional[Callable[[IperfResult], bool]] = None) -> Dict[int, List[IperfResult]]:
        return self._dict_by_key('ap_ssid', filter_fn)

    def draw_att_vs_rssi_chart(
        self,
        filename: str,
        filter_fn: Optional[Callable[[IperfResult], bool]] = None,
        with_keys: Optional[List[str]] = None,
    ) -> None:
        # Needs extra packages to draw the chart
        pass

    def draw_rssi_vs_rate_chart(
        self,
        filename: str,
        filter_fn: Optional[Callable[[IperfResult], bool]] = None,
        with_keys: Optional[List[str]] = None,
    ) -> None:
        # Needs extra packages to draw the chart
        pass


# class NotUsed:
#     PC_BANDWIDTH_LOG_PATTERN
# = re.compile(r'(\d+\.\d+)\s*-\s*(\d+.\d+)\s+sec\s+[\d.]+\s+MBytes\s+([\d.]+)\s+Mbits\/sec')
#     DUT_BANDWIDTH_LOG_PATTERN = re.compile(r'([\d.]+)-\s*([\d.]+)\s+sec\s+([\d.]+)\s+Mbits/sec')

#     ZERO_POINT_THRESHOLD = -88  # RSSI, dbm
#     ZERO_THROUGHPUT_THRESHOLD = -92  # RSSI, dbm
#     BAD_POINT_RSSI_THRESHOLD = -75  # RSSI, dbm
#     BAD_POINT_MIN_THRESHOLD = 10  # Mbps
#     BAD_POINT_PERCENTAGE_THRESHOLD = 0.3

#     # we need at least 1/2 valid points to qualify the test result
#     THROUGHPUT_QUALIFY_COUNT = 3

#     RSSI_RANGE = [-x for x in range(10, 100)]
#     ATT_RANGE = [x for x in range(0, 64)]

#     def __init__(self, proto, direction, config_name, reverse=None):  # type: (str, str, str) -> None
#         self.proto = proto
#         self.direction = direction
#         self.config_name = config_name
#         self.throughput_by_rssi = dict()  # type: dict
#         self.throughput_by_att = dict()  # type: dict
#         self.att_rssi_map = dict()  # type: dict
#         self.ht_ssid = dict()  # type: dict
#         self.heap_size = INVALID_HEAP_SIZE
#         self.error_list = []  # type: list[str]
#         self.reverse = reverse

#     # type: (float, str, int, int, str) -> None
#     def _save_result(self, throughput, ap_ssid, att, rssi, heap_size, ht_value):
#         """
#         save the test results:

#         * record the better throughput if att/rssi is the same.
#         * record the min heap size.
#         * record bandwidth after negotiation
#         """
#         type_ssid = f'{self.reverse}_{ap_ssid}' if self.reverse else ap_ssid
#         if type_ssid not in self.att_rssi_map:
#             # for new ap, create empty dict()
#             self.throughput_by_att[type_ssid] = dict()
#             self.throughput_by_rssi[type_ssid] = dict()
#             self.att_rssi_map[type_ssid] = dict()
#             self.ht_ssid[type_ssid] = list()

#         self.att_rssi_map[type_ssid][att] = rssi
#         self.ht_ssid[type_ssid].append(ht_value)

#         def record_throughput(database, key_value):  # type: (dict, int) -> None
#             try:
#                 # we save the larger value for same att
#                 if throughput > database[type_ssid][key_value]:
#                     database[type_ssid][key_value] = throughput
#             except KeyError:
#                 database[type_ssid][key_value] = throughput

#         record_throughput(self.throughput_by_att, att)
#         record_throughput(self.throughput_by_rssi, rssi)

#         if int(heap_size) < self.heap_size:
#             self.heap_size = int(heap_size)

#     # type: (str, str, int, int, str) -> float
#     def add_result(self, raw_data, ap_ssid, att, rssi, heap_size, ht_value):
#         """
#         add result for one test

#         :param raw_data: iperf raw data
#         :param ap_ssid: ap ssid that tested
#         :param att: attenuate value
#         :param rssi: AP RSSI
#         :param heap_size: min heap size during test
#         :param ht_value: the bandwidth after negotiation
#         :return: throughput
#         """
#         fall_to_0_recorded = 0
#         throughput_list = []
#         result_list = self.PC_BANDWIDTH_LOG_PATTERN.findall(raw_data)
#         if not result_list:
#             # failed to find raw data by PC pattern, it might be DUT pattern
#             result_list = self.DUT_BANDWIDTH_LOG_PATTERN.findall(raw_data)
#         avg_throughput = 0.0
#         for result in result_list:
#             t_start = float(result[0])
#             t_end = float(result[1])
#             throughput = float(result[2])
#             if int(t_end - t_start) > 1:
#                 # this could be summary, ignore this
#                 # Notice this is not compatible with iperf2
#                 avg_throughput = throughput
#                 continue
#             if throughput == 0.00 and rssi > self.ZERO_POINT_THRESHOLD:
#                 # throughput fall to 0 Error. we only record 1 records for one test
#                 self.error_list.append(
#                     '[Error][Throughput Drop to 0][{}][att: {}][rssi: {}]: 0 throughput interval: ' '{}-{}'.format(
#                         ap_ssid, att, rssi, result[0], result[1]
#                     )
#                 )
#                 fall_to_0_recorded += 1
#                 continue
#             throughput_list.append(throughput)

#         if fall_to_0_recorded > self.THROUGHPUT_QUALIFY_COUNT:
#             self.error_list.append(
#                 '[Error][Fatal][{} {}][{}][att: {}][rssi: {}]: Only {} '
#                 'throughput values found, expected at least {}'.format(
#                     self.proto, self.direction, ap_ssid, att, rssi, len(throughput_list),
#                     self.THROUGHPUT_QUALIFY_COUNT
#                 )
#             )
#         if avg_throughput == float(0) and rssi > self.ZERO_THROUGHPUT_THRESHOLD:
#             self.error_list.append(
#                 '[Error][Fatal][{} {}][{}][att: {}][rssi: {}]: No throughput data found'.format(
#                     self.proto, self.direction, ap_ssid, att, rssi
#                 )
#             )
#             if len(throughput_list):
#                 avg_throughput = sum(throughput_list) / len(throughput_list)
#         if avg_throughput != float(0) and rssi > self.BAD_POINT_RSSI_THRESHOLD:
#             if (
#                 max(throughput_list) - avg_throughput > avg_throughput * 0.33
#                 or avg_throughput - min(throughput_list) > avg_throughput * 0.33
#             ):
#                 self.error_list.append(
#                     '[Error][Fatal][{} {}][{}][att: {}][rssi: {}]: throughput values vary too large!'.format(
#                         self.proto, self.direction, ap_ssid, att, rssi
#                     )
#                 )
#                 logger.error(
#                     '[Error][{} {}][{}][att: {}][rssi: {}]: throughput values vary too large!\n'
#                     'Max: {:.2f}\t Min: {:.2f}\t Avg: {:.2f}\t\n'.format(
#                         self.proto,
#                         self.direction,
#                         ap_ssid,
#                         att,
#                         rssi,
#                         max(throughput_list),
#                         min(throughput_list),
#                         avg_throughput,
#                     )
#                 )
#         self._save_result(round(avg_throughput, 2), ap_ssid, att, rssi, heap_size, ht_value)

#         return avg_throughput

#     def post_analysis(self):  # type: () -> None
#         """
#         some rules need to be checked after we collected all test raw data:

#         1. throughput value 30% worse than the next point with lower RSSI
#         2. throughput value 30% worse than the next point with larger attenuate
#         """

#         def analysis_bad_point(data, index_type):  # type: (dict, str) -> None
#             for ap_ssid in data:
#                 result_dict = data[ap_ssid]
#                 index_list = list(result_dict.keys())
#                 index_list.sort()
#                 if index_type == 'att':
#                     index_list.reverse()

#                 for i, index_value in enumerate(index_list[1:]):
#                     if (
#                         index_value < self.BAD_POINT_RSSI_THRESHOLD
#                         or result_dict[index_list[i]] < self.BAD_POINT_MIN_THRESHOLD
#                     ):
#                         continue
#                     _percentage = result_dict[index_value] / result_dict[index_list[i]]
#                     if _percentage < 1 - self.BAD_POINT_PERCENTAGE_THRESHOLD:
#                         self.error_list.append(
#                             '[Error][Bad point][{}][{}: {}]: drop {:.02f}%'.format(
#                                 ap_ssid, index_type, index_value, (1 - _percentage) * 100
#                             )
#                         )

#         analysis_bad_point(self.throughput_by_rssi, 'rssi')
#         analysis_bad_point(self.throughput_by_att, 'att')

#     # type: (str, str, str) -> str
#     def draw_throughput_figure(self, path, ap_ssid, draw_type):
#         """
#         :param path: folder to save figure. make sure the folder is already created.
#         :param ap_ssid: ap ssid string or a list of ap ssid string
#         :param draw_type: "att" or "rssi"
#         :return: file_name
#         """
#         if draw_type == 'rssi':
#             type_name = 'RSSI'
#             data = self.throughput_by_rssi
#             range_list = self.RSSI_RANGE
#         elif draw_type == 'att':
#             type_name = 'Att'
#             data = self.throughput_by_att
#             range_list = self.ATT_RANGE
#         else:
#             raise AssertionError('draw type not supported')
#         if isinstance(ap_ssid, list):
#             file_name = 'ThroughputVs{}_{}_{}.html'.format(type_name, self.proto, self.direction)
#         else:
#             file_name = 'ThroughputVs{}_{}_{}.html'.format(type_name, self.proto, self.direction)

#         LineChart.draw_line_chart(
#             os.path.join(path, file_name),
#             'Throughput Vs {} ({} {})'.format(type_name, self.proto, self.direction),
#             '{} (dbm)'.format(type_name),
#             'Throughput (Mbps)',
#             data,
#             range_list,
#         )
#         return file_name

#     def draw_rssi_vs_att_figure(self, path, ap_ssid):  # type: (str, str) -> str
#         """
#         :param path: folder to save figure. make sure the folder is already created.
#         :param ap_ssid: ap to use
#         :return: file_name
#         """
#         if isinstance(ap_ssid, list):
#             file_name = 'AttVsRSSI.html'
#         else:
#             file_name = 'AttVsRSSI.html'
#         LineChart.draw_line_chart(
#             os.path.join(path, file_name), 'Att Vs RSSI', 'Att (dbm)', 'RSSI (dbm)', self.att_rssi_map, self.ATT_RANGE
#         )
#         return file_name

#     def __str__(self):  # type: () -> str
#         """
#         returns summary for this test:

#         1. test result (success or fail)
#         2. best performance for each AP
#         3. min free heap size during test
#         """
#         if self.throughput_by_att:
#             ret = '[{}_{}][{}]: {}\r\n\r\n'.format(
#                 self.proto, self.direction, self.config_name, 'Fail' if self.error_list else 'Success'
#             )
#             ret += 'Performance for each AP:\r\n'
#             for ap_ssid in self.throughput_by_att:
#                 if len(set(self.ht_ssid[ap_ssid])) != 1:
#                     logging.info('The negotiation result not compile during the tests.')
#                 ht_ssid = self.ht_ssid[ap_ssid][0]
#                 ret += '[{}][BW: {}Mhz]: {:.02f} Mbps\r\n'.format(
#                     ap_ssid, ht_ssid, max(self.throughput_by_att[ap_ssid].values())
#                 )
#             if self.heap_size != INVALID_HEAP_SIZE:
#                 ret += 'Minimum heap size: {}'.format(self.heap_size)
#         else:
#             ret = ''
#         return ret
