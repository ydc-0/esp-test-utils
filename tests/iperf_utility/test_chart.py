import pytest

from esp_test_utils.iperf_utility import line_chart

try:
    import pyecharts  # noqa: F401

    PYECHARTS_INSTALLED = True
except ImportError:
    PYECHARTS_INSTALLED = False


@pytest.mark.skipif(PYECHARTS_INSTALLED, reason='Only run this case if pyecharts is not installed.')
def test_pyecharts_not_installed() -> None:
    with pytest.raises(ImportError) as e:
        line_chart.draw_line_chart_basic('file_name', 'title', [{'a': 1}])
    assert 'please install pyecharts' in e.value.msg


@pytest.mark.skipif(not PYECHARTS_INSTALLED, reason='Only run this case if pyecharts is installed.')
def test_draw_line_charts(tmp_path) -> None:
    file_name = str(tmp_path / 'charts.html')
    y_data = [
        {'a': 1},
        {'a': 2},
        {'a': 2},
    ]
    line_chart.draw_line_chart_basic(file_name, 'title', y_data)
    # No exceptions


if __name__ == '__main__':
    # Breakpoints do not work with coverage, disable coverage for debugging
    pytest.main([__file__, '--no-cov', '--log-cli-level=DEBUG'])
