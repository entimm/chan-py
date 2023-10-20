import yfinance as yf

from common.const import AuType, DataField, LvType
from common.func_util import parse_normal_date_str, str2float
from data_fetch.abs_stock_api import AbsStockApi


class YFinanceFetcher(AbsStockApi):
    def __init__(self, code, k_type=LvType.K_DAY, begin_date=None, end_date=None, autype=AuType.QFQ):
        super(YFinanceFetcher, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        autype_dict = {AuType.QFQ: True, AuType.HFQ: False, AuType.NONE: None}
        ticker = yf.Ticker(self.code)
        intraday_data = ticker.history(
            start=self.begin_date,
            end=self.end_date,
            interval=self.__convert_period_type(),
            actions=autype_dict[self.autype],
        )

        for index, row in intraday_data.iterrows():
            data_dict = {
                DataField.FIELD_TIME: parse_normal_date_str(index.strftime("%Y-%m-%d %H:%M:%S")),
                DataField.FIELD_OPEN: str2float(row["Open"]),
                DataField.FIELD_HIGH: str2float(row["High"]),
                DataField.FIELD_LOW: str2float(row["Low"]),
                DataField.FIELD_CLOSE: str2float(row["Close"]),
                DataField.FIELD_VOLUME: str2float(row["Volume"])
            }

            yield data_dict, False

    def __convert_period_type(self):
        _dict = {
            LvType.K_DAY: '1d',
            LvType.K_WEEK: '1wk',
            LvType.K_MON: '1mo',
            LvType.K_1M: '1m',
            LvType.K_5M: '5m',
            LvType.K_15M: '15m',
            LvType.K_30M: '30m',
            LvType.K_60M: '60m',
        }
        return _dict[self.k_type]
