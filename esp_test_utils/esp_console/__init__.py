from iperf_cmd import IperfCmd
from ota_cmd import OTACmd
from wifi_cmd import WifiCmd


class ConsoleMixin(WifiCmd, OTACmd, IperfCmd):
    pass
