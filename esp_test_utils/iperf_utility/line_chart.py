from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from ..basic.decorators import enhance_import_error_message
from ..logger import get_logger

logger = get_logger('iperf-util')


@enhance_import_error_message('please install pyecharts or "pip install esp-test-utils[chart]"')
def draw_line_chart_basic(
    file_name: str,
    title: str,
    y_data: List[Dict[str, float]],
    x_data: Optional[List[Union[str, float]]] = None,
    x_label: str = 'x',
    y_label: str = 'y',
):
    """Draw line chart and save to file.

    Args:
        file_name (str): line chart render file name
        title (str): title of the chart
        y_data (List[Dict[str, float]]): list of chart data, format eg: [{'y1': 1, 'y2': 1}, {'y1': 2, 'y2': 1}]
        x_data (Optional[List[float]], optional): x data. Defaults to "range(len(y_data))".
        x_label (str, optional): x label name. Defaults to 'x'.
        y_label (str, optional): y label name. Defaults to 'y'.
    """
    # pylint: disable=too-many-arguments
    import pyecharts.options as opts
    from pyecharts.charts import Line

    assert len(y_data) > 0
    if not x_data:
        x_data = list(range(len(y_data)))
    assert len(x_data) == len(y_data)
    if any((isinstance(x, (int, float)) and x < 0 for x in x_data)):
        # echarts do not support minus number for x axis, convert to string
        x_data = list(map(str, x_data))

    line = Line()
    line.add_xaxis(x_data)

    y_names = y_data[0].keys()
    for name in y_names:
        legend = name
        _data = [y[name] for y in y_data]
        if all((isinstance(y, (int, float)) for y in _data)):
            # show max/min
            legend += f' (max: {max(_data)}, min: {min(_data)})'
        line.add_yaxis(legend, _data, is_smooth=True)
    line.set_global_opts(
        datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
        title_opts=opts.TitleOpts(title=title, pos_left='center'),
        legend_opts=opts.LegendOpts(pos_top='10%', pos_left='right', orient='vertical'),
        tooltip_opts=opts.TooltipOpts(trigger='axis'),
        xaxis_opts=opts.AxisOpts(type_='category', name=x_label, splitline_opts=opts.SplitLineOpts(is_show=True)),
        yaxis_opts=opts.AxisOpts(
            type_='value',
            name=y_label,
            axistick_opts=opts.AxisTickOpts(is_show=True),
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
    )
    line.render(file_name)
