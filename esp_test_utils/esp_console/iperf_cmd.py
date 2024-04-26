import re


class IperfCmd:
    """For esp-console based iperf-cmd: https://components.espressif.com/components/espressif/iperf-cmd

    Supported Versions: v0.1.x

    Basic example:
        ```
        from esp_test_utils.esp_console import IperfCmd
        ...
        dut.write('iperf -s')
        match = dut.expect(IperfCmd.BANDWIDTH_LOG_PATTERN)
        ```
    """

    VERSION = '0.1'

    BANDWIDTH_LOG_PATTERN = re.compile(r'([\d.]+)-\s*([\d.]+)\s+sec\s+([\d.]+)\s+Mbits/sec')
    # TCP client (v0.1) shows "Successfully connected". others show "Socket created"
    # It is recommended to wait a while after the iperf server is running before running the iperf client.
    IPERF_STARTED_PATTERN = re.compile(r'Socket created|Successfully connected')
    # Iperf stop
    IPERF_STOP_CMD = 'iperf --abort'
    IPERF_STOPPED_PATTERN = 'IPERF_STOP,OK'
