import re
from typing import List
from typing import Optional

from ..adapter.dut import DutWrapper
from ..logger import get_logger
from .iperf_results import IperfResult
from .iperf_results import IperfResultsRecord


logger = get_logger('iperf-util')


class IperfDataParser:
    PC_BANDWIDTH_LOG_PATTERN = re.compile(
        r'(\d+\.\d+)\s*-\s*(\d+.\d+)\s+sec\s+[\d.]+\s+MBytes\s+([\d.]+)\s+([MK]bits/sec)'
    )
    DUT_BANDWIDTH_LOG_PATTERN = re.compile(r'([\d.]+)-\s*([\d.]+)\s+sec\s+([\d.]+)\s+([MK]bits/sec)')

    def __init__(self, raw_data: str, transmit_time: int = 0):
        self.raw_data = raw_data
        self.transmit_time = transmit_time
        self._avg_throughput = 0
        self._throughput_list = []
        self.error_list = []
        self._unit = ''
        self._parse_data()

    def _parse_data(self):
        match_list = list(self.PC_BANDWIDTH_LOG_PATTERN.finditer(self.raw_data))
        if not match_list:
            # failed to find raw data by PC pattern, it might be DUT pattern
            match_list = list(self.DUT_BANDWIDTH_LOG_PATTERN.finditer(self.raw_data))
        if not match_list:
            raise ValueError('Can not parse data!')

        _current_end = 0.0
        _interval = 0
        for match in match_list:
            t_start = float(match.group(1))
            t_end = float(match.group(2))
            # ignore if report time larger than given transmit time.
            if self.transmit_time and t_end > self.transmit_time:
                logger.debug(f'ignore iperf report {t_start} - {t_end}: {match.group(3)} {match.group(4)}')
                continue
            # Check if there are unexpected times
            if _current_end and t_start and t_start != _current_end:
                self.error_list.append(f'Missing iperf data from {_current_end} to {t_start}')
            _current_end = t_end
            # get match results
            self._unit = match.group(4)
            throughput = float(match.group(3))
            if not _interval and len(match_list) > 1:
                _interval = t_end - t_start
            if _interval and int(t_end - t_start) > _interval:
                # this could be the summary, got average throughput
                self._avg_throughput = throughput
                continue
            if throughput == 0.00:
                self.error_list.append(f'Throughput drop to 0 at {t_start}-{t_end}')
                # still put it into list though throughput is zero
            self._throughput_list.append(throughput)

    @property
    def avg(self) -> float:
        if self._avg_throughput:
            return self._avg_throughput
        if self._throughput_list:
            return sum(self._throughput_list) / len(self._throughput_list)
        raise ValueError('Failed to get throughput from data.')

    @property
    def max(self) -> float:
        if self._throughput_list:
            return max(self._throughput_list)
        raise ValueError('Failed to get throughput from data.')

    @property
    def min(self) -> float:
        if self._throughput_list:
            return min(self._throughput_list)
        raise ValueError('Failed to get throughput from data.')

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def throughput_list(self) -> List[float]:
        return self._throughput_list


class IperfTestBaseUtility:
    IPERF_EXTRA_OPTIONS = []
    IPERF_REPORT_INTERVAL = 1
    # IPERF_EXTRA_OPTIONS = ['-f', 'm']
    DEF_UDP_RX_BW_LIMIT = {
        # Mbits/sec
        'esp32c2': 60,
        'esp32c3': 70,
        'esp32s2': 85,
        'esp32c6': 70,
        'default': 100,
    }
    TEST_TYPES = ['tcp_tx', 'tcp_rx', 'udp_tx', 'udp_rx']

    def __init__(
        self,
        dut: DutWrapper,
        remote: Optional[DutWrapper] = None,
    ):
        self.dut = dut
        self.remote = remote
        self.udp_rx_bw_limit = self.DEF_UDP_RX_BW_LIMIT.copy()
        self.test_types = self.TEST_TYPES.copy()
        self.results = IperfResultsRecord()

    @property
    def dut_ip(self):
        raise NotImplementedError('')

    @property
    def remote_ip(self):
        raise NotImplementedError('')

    def setup(self) -> None:
        raise NotImplementedError()

    def teardown(self) -> None:
        raise NotImplementedError()

    def run_one_case(self, test_type: str) -> IperfResult:
        raise NotImplementedError()

    def run_all_cases(self):
        self.setup()
        try:
            for test_type in self.test_types:
                _res = self.run_one_case(test_type)
                self.results.append_result(_res)
        finally:
            self.teardown()


# class IperfTestUtility(object):
#     """iperf test implementation"""

#     SCAN_AP_RETRY_COUNT = 3
#     REBOOT_BEFORE_TEST = True
#     RECONNECT_BEFORE_TEST = True

#     ZERO_POINT_THRESHOLD = -88  # RSSI, dbm
#     ZERO_THROUGHPUT_THRESHOLD = -92  # RSSI, dbm
#     BAD_POINT_RSSI_THRESHOLD = -75  # RSSI, dbm
#     BAD_POINT_MIN_THRESHOLD = 10  # Mbps
#     BAD_POINT_PERCENTAGE_THRESHOLD = 0.3

#     # we need at least 1/2 valid points to qualify the test result
#     THROUGHPUT_QUALIFY_COUNT = 3

#     def __init__(
#         self,
#         target: str,
#         dut: DutWrapper,
#         ap_ssid: str,
#         ap_password: str = '',
#         test_ipv6: bool = False,
#         # Use softap rather than PC
#         softap_dut: Optional[DutWrapper] = None,
#         log_file: str = '',
#         bind_pc_ip: str = '',
#         # must
#         # chip: str = 'not_set',
#         # config_name: str = 'not_set',
#     ) -> None:
#         self.config_name = config_name
#         self.dut = dut
#         self.chip = chip
#         self.pc_iperf_log_file = pc_iperf_log_file
#         self.ap_ssid = ap_ssid
#         self.ap_password = ap_password
#         self.pc_nic_ip = pc_nic_ip
#         self.fail_to_scan = 0
#         self.lowest_rssi_scanned = 0

#         if test_result:
#             if self.config_name == 'reverse':
#                 for value in test_result.values():
#                     value.reverse = 'reverse'
#             self.test_result = test_result
#         else:
#             self.test_result = {
#                 'tcp_tx': TestResult('tcp', 'tx', config_name),
#                 'tcp_rx': TestResult('tcp', 'rx', config_name),
#                 'udp_tx': TestResult('udp', 'tx', config_name),
#                 'udp_rx': TestResult('udp', 'rx', config_name),
#             }
#         self.sta_config = sta_config

#     def setup(self):  # type: (Any) -> Tuple[str,int]
#         """
#         setup iperf test:

#         1. reboot DUT (currently iperf is not very robust, need to reboot DUT)
#         2. scan to get AP's RSSI
#         3. connect to AP
#         """
#         time.sleep(1)
#         # self.dut.write('restart')
#         # self.dut.expect('boot:')
#         # self.dut.expect('iperf>')
#         # time.sleep(1)
#         self.dut.write('sta_scan {}'.format(self.ap_ssid))
#         for _ in range(self.SCAN_AP_RETRY_COUNT):
#             try:
#                 rssi = int(
#                     self.dut.expect(re.compile(r'\[{}]\[rssi=(-\d+)]'.format(self.ap_ssid)), timeout=SCAN_TIMEOUT)[0]
#                 )
#                 break
#             except Exception:
#                 continue
#         else:
#             raise AssertionError('Failed to scan AP')

#         self.dut.write('wifi status')
#         try:
#             self.dut.expect('STA_CONNECTED')
#             # STA_IP4 -> STA_IP
#             dut_ip = self.dut.expect(re.compile(r'STA_IP4?:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[^\d]'), timeout=5)[0]
#         except TimeoutError:
#             raise AssertionError('Failed to connect AP')

#         return dut_ip, rssi, self.ht_value

#     def connect_ap(self) -> Tuple[str, int]:
#         self.dut.write('restart')
#         self.dut.expect('iperf>')
#         time.sleep(3)
#         if self.sta_config and isinstance(self.sta_config, dict):
#             protocol = self.sta_config.get('protocol')
#             bw = self.sta_config.get('bw')
#             if protocol:
#                 self.dut.write(f'wifi_protocol {protocol} -i sta')
#                 self.dut.expect('OK')
#             if bw:
#                 self.dut.write(f'wifi_bandwidth {bw} -i sta')
#                 self.dut.expect('OK')
#         for _ in range(RETRY_COUNT):
#             try:
#                 self.dut.write('sta_connect {} {}'.format(self.ap_ssid, self.ap_password))
#                 self.ht_value = self.dut.expect(
#                     re.compile(r'wifi:connected with .+, aid = \d+, channel \d+, (.+), bssid = .+')
#                 )[0]
#                 self.dut.expect(re.compile(r'sta ip: ([\d.]+), mask: ([\d.]+), gw: ([\d.]+)'), timeout=10)[0]
#                 break
#             except DUT.ExpectTimeout:
#                 continue
#         else:
#             raise AssertionError('Failed to connect AP')

#     def teardown(self) -> Tuple[str, int]:
#         """
#         1. kill iperf process
#         2. set mode to sta do disconnect.
#         """
#         subprocess.run('sudo killall iperf 2>&1 > /dev/null', shell=True)
#         for _ in range(2):
#             try:
#                 self.dut.write('iperf --abort')
#                 self.dut.expect('DONE.IPERF_STOP,OK.')
#                 break
#             except DUT.ExpectTimeout:
#                 time.sleep(10)

#     # type: (str, str, int, int, int) -> Any
#     def _save_test_result(self, test_case, raw_data, att, rssi, heap_size, ht_value):
#         return self.test_result[test_case].add_result(raw_data, self.ap_ssid, att, rssi, heap_size, ht_value)

#     # type: (Any, str, str, int) -> Tuple[str, int, int]
#     def _test_once(self, proto, direction, bw_limit):
#         """do measure once for one type"""
#         # connect and scan to get RSSI
#         dut_ip, rssi, ht_value = self.setup()
#         checker_timeout = TEST_TIMEOUT + 5
#         assert direction in ['rx', 'tx']
#         assert proto in ['tcp', 'udp']
#         test_method = '{}_{}'.format(proto, direction)
#         bw = 0
#         if bw_limit:
#             bw = BW_LIMIT[self.chip.lower()][test_method]
#         # run iperf test
#         if direction == 'tx':
#             with open(PC_IPERF_TEMP_LOG_FILE, 'w') as f:
#                 if proto == 'tcp':
#                     process = subprocess.Popen(
#                         ['iperf', '-s', '-B', self.pc_nic_ip, '-t', str(TEST_TIME + 1), '-i', '1', '-f', 'm'],
#                         stdout=f,
#                         stderr=f,
#                     )
#                     time.sleep(0.5)
#                     if bw:
#                         self.dut.write('iperf -c {} -i 1 -t {} -b {}'.format(self.pc_nic_ip, TEST_TIME, bw))
#                     else:
#                         self.dut.write('iperf -c {} -i 1 -t {}'.format(self.pc_nic_ip, TEST_TIME))
#                 else:
#                     process = subprocess.Popen(
#                         ['iperf', '-s', '-u', '-B', self.pc_nic_ip, '-t', str(TEST_TIME), '-i', '1', '-f', 'm'],
#                         stdout=f,
#                         stderr=f,
#                     )
#                     if bw:
#                         self.dut.write('iperf -c {} -u -i 1 -t {} -b {}'.format(self.pc_nic_ip, TEST_TIME, bw))
#                     else:
#                         self.dut.write('iperf -c {} -u -i 1 -t {}'.format(self.pc_nic_ip, TEST_TIME))

#                 for _ in range(checker_timeout):
#                     if process.poll() is not None:
#                         break
#                     time.sleep(1)
#                 else:
#                     process.terminate()

#             with open(PC_IPERF_TEMP_LOG_FILE, 'r') as f:
#                 pc_raw_data = server_raw_data = f.read()
#         else:
#             with open(PC_IPERF_TEMP_LOG_FILE, 'w') as f:
#                 if proto == 'tcp':
#                     self.dut.write('iperf -s -i 1 -t {}'.format(TEST_TIME))
#                     # wait until DUT TCP server created
#                     try:
#                         self.dut.expect('Socket created', timeout=5)
#                     except DUT.ExpectTimeout:
#                         # compatible with old iperf example binary
#                         logger.error('create iperf tcp server fail')
#                     if bw:
#                         process = subprocess.Popen(
#                             ['iperf', '-c', dut_ip, '-b', str(bw) + 'm', '-t', str(TEST_TIME), '-f', 'm'],
#                             stdin=f,
#                             stdout=f,
#                             stderr=f,
#                         )
#                     else:
#                         process = subprocess.Popen(
#                             ['iperf', '-c', dut_ip, '-t', str(TEST_TIME), '-f', 'm'], stdin=f, stdout=f, stderr=f
#                         )
#                     for _ in range(checker_timeout):
#                         if process.poll() is not None:
#                             break
#                         time.sleep(1)
#                     else:
#                         process.terminate()
#                 else:
#                     self.dut.write('iperf -s -u -i 1 -t {}'.format(TEST_TIME))
#                     # wait until DUT TCP server created
#                     try:
#                         self.dut.expect('Socket created', timeout=5)
#                     except DUT.ExpectTimeout:
#                         # compatible with old iperf example binary
#                         logger.error('create iperf udp server fail')
#                     if bw:
#                         process = subprocess.Popen(
#                             ['iperf', '-c', dut_ip, '-u', '-b', str(bw) + 'm', '-t', str(TEST_TIME), '-f', 'm'],
#                             stdin=f,
#                             stdout=f,
#                             stderr=f,
#                         )
#                         for _ in range(checker_timeout):
#                             if process.poll() is not None:
#                                 break
#                             time.sleep(1)
#                         else:
#                             process.terminate()
#                     else:
#                         # set default udp send rate to 100Mbps
#                         process = subprocess.Popen(
#                             ['iperf', '-c', dut_ip, '-u', '-b', '100m', '-t', str(TEST_TIME), '-f', 'm'],
#                             stdin=f,
#                             stdout=f,
#                             stderr=f,
#                         )
#                         for _ in range(checker_timeout):
#                             if process.poll() is not None:
#                                 break
#                             time.sleep(1)
#                         else:
#                             process.terminate()
#             time.sleep(1)
#             server_raw_data = self.dut.read()
#             with open(PC_IPERF_TEMP_LOG_FILE, 'r') as f:
#                 pc_raw_data = f.read()

#         # save PC iperf logs to console
#         with open(self.pc_iperf_log_file, 'a+') as f:
#             f.write(
#                 '## [{}] `{}`\r\n##### {}'.format(
#                     self.config_name,
#                     '{}_{}'.format(proto, direction),
#                     time.strftime('%m-%d %H:%M:%S', time.localtime(time.time())),
#                 )
#             )
#             f.write('\r\n```\r\n\r\n' + pc_raw_data + '\r\n```\r\n')
#         self.dut.write('heap')
#         heap_size = self.dut.expect(re.compile(r'MIN_HEAPSIZE:(\d+)\D'))[0]

#         # return server raw data (for parsing test results) and RSSI
#         return server_raw_data, rssi, heap_size, ht_value

#     # type: (str, str, int, int) -> None
#     def run_test(self, proto, direction, atten_val, bw_limit):
#         """
#         run test for one type, with specified atten_value and save the test result

#         :param proto: tcp or udp
#         :param direction: tx or rx
#         :param atten_val: attenuate value
#         """
#         rssi = FAILED_TO_SCAN_RSSI
#         heap_size = INVALID_HEAP_SIZE
#         try:
#             server_raw_data, rssi, heap_size, ht_value = self._test_once(proto, direction, bw_limit)
#             throughput = self._save_test_result(
#                 '{}_{}'.format(proto, direction), server_raw_data, atten_val, rssi, heap_size, ht_value
#             )
#             logger.info(
#                 '[{}][{}_{}][{}][{}][{}]: {:.02f}'.format(
#                     self.config_name, proto, direction, rssi, self.ap_ssid, ht_value, throughput
#                 )
#             )
#             self.lowest_rssi_scanned = min(self.lowest_rssi_scanned, rssi)
#         except (ValueError, IndexError):
#             self._save_test_result('{}_{}'.format(proto, direction), '', atten_val, rssi, heap_size, ht_value)
#             logger.error('Fail to get throughput results.')
#         except AssertionError:
#             self.fail_to_scan += 1
#             logger.error('Fail to scan or connect AP.')
#         finally:
#             self.teardown()

#     def run_all_cases(self, atten_val, bw_limit, test_types=None):  # type: (int, int) -> None
#         """
#         run test for all types (udp_tx, udp_rx, tcp_tx, tcp_rx).

#         :param atten_val: attenuate value
#         :param bw_limit: throughput bandwidth limit
#         :param test_type: list of test type: eg: ['tcp_tx']
#         """
#         if not test_types:
#             test_types = ['tcp_tx', 'tcp_rx', 'udp_tx', 'udp_rx']
#         for _test in test_types:
#             proto, direction = _test.split('_')
#             self.run_test(proto, direction, atten_val, bw_limit)
#             if self.fail_to_scan > 5 or self.lowest_rssi_scanned < FAILED_TO_SCAN_RSSI:
#                 raise AssertionError

#     def wait_ap_power_on(self):  # type: (Any) -> bool
#         """
#         AP need to take sometime to power on. It changes for different APs.
#         This method will scan to check if the AP powers on.

#         :return: True or False
#         """
#         # self.dut.write('restart')
#         # self.dut.expect('boot:')
#         # self.dut.expect('iperf>')
#         for _ in range(WAIT_AP_POWER_ON_TIMEOUT // SCAN_TIMEOUT):
#             try:
#                 self.dut.write('sta_scan {}'.format(self.ap_ssid))
#                 self.dut.expect(re.compile(r'\[{}]\[rssi=(-\d+)]'.format(self.ap_ssid)), timeout=SCAN_TIMEOUT)
#                 ret = True
#                 break
#             except DUT.ExpectTimeout:
#                 pass
#         else:
#             ret = False
#         return ret

#     def get_best_throughput(self, test_type, ap_ssid):  # type: () -> Any
#         """get the best throughput during test"""
#         best_for_aps = max(self.test_result[test_type].throughput_by_att[ap_ssid].values())
#         return best_for_aps


# class IperfTestUtilityRvR(IperfTestUtility):
#     "Iperf RvR (Rate vs Range) test utility"

#     pass
