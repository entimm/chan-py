from datetime import datetime

import ccxt

from common.const import AUTYPE, DATA_FIELD, KL_TYPE
from common.func_util import create_item_dict
from data_fetch.abs_stock_api import AbsStockApi


class CcxtFetcher(AbsStockApi):
    is_connect = None

    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=AUTYPE.QFQ):
        super(CcxtFetcher, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        fields = "time,open,high,low,close"
        exchange = ccxt.binance()
        timeframe = self.__convert_period_type()
        since_date = exchange.parse8601(f'{self.begin_date}T00:00:00')
        data = exchange.fetch_ohlcv(self.code, timeframe, since=since_date)

        for item in data:
            time_obj = datetime.fromtimestamp(item[0] / 1000)
            time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
            item_data = [
                time_str,
                item[1],
                item[2],
                item[3],
                item[4]
            ]
            yield create_item_dict(item_data, self.columnNameMap(fields)), True

    def __convert_period_type(self):
        _dict = {
            KL_TYPE.K_DAY: '1d',
            KL_TYPE.K_WEEK: '1w',
            KL_TYPE.K_MON: '1M',
            KL_TYPE.K_5M: '5m',
            KL_TYPE.K_15M: '15m',
            KL_TYPE.K_30M: '30m',
            KL_TYPE.K_60M: '1h',
        }
        return _dict[self.k_type]

    def columnNameMap(self, fileds: str):
        _dict = {
            "time": DATA_FIELD.FIELD_TIME,
            "open": DATA_FIELD.FIELD_OPEN,
            "high": DATA_FIELD.FIELD_HIGH,
            "low": DATA_FIELD.FIELD_LOW,
            "close": DATA_FIELD.FIELD_CLOSE,
        }
        return [_dict[x] for x in fileds.split(",")]
