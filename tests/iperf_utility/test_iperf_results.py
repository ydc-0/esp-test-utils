import pytest

from esp_test_utils.iperf_utility.iperf_results import IperfResult
from esp_test_utils.iperf_utility.iperf_results import IperfResultsRecord


def test_iperf_result_to_dict():
    res = IperfResult(avg=100, rssi=-10)
    d = res.to_dict()
    assert d['avg'] == 100
    assert d['rssi'] == -10
    assert 'type' not in d


def test_iperf_record(tmp_path):
    record = IperfResultsRecord()
    for att in [1, 2, 3, 4, 5]:
        _res = IperfResult(avg=100, rssi=-10, ap_ssid='ap1')
        record.append_result(_res)
        _res = IperfResult(avg=90, rssi=-10, ap_ssid='ap2')
        record.append_result(_res)
    _file = str(tmp_path / 'chart1.html')
    record.draw_att_vs_rssi_chart(_file)
    _file = str(tmp_path / 'chart1.html')
    record.draw_rssi_vs_rate_chart()


if __name__ == '__main__':
    # Breakpoints do not work with coverage, disable coverage for debugging
    pytest.main([__file__, '--no-cov', '--log-cli-level=DEBUG'])
