import yfinance as yf

from common.const import AUTYPE, DATA_FIELD, KL_TYPE
from common.func_util import parse_normal_date_str, str2float
from data_fetch.abs_stock_api import AbsStockApi


class YFinanceFetcher(AbsStockApi):
    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=AUTYPE.QFQ):
        super(YFinanceFetcher, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        autype_dict = {AUTYPE.QFQ: True, AUTYPE.HFQ: False, AUTYPE.NONE: None}
        ticker = yf.Ticker(self.code)
        intraday_data = ticker.history(
            start=self.begin_date,
            end=self.end_date,
            interval=self.__convert_period_type(),
            actions=autype_dict[self.autype],
        )

        for index, row in intraday_data.iterrows():
            data_dict = {
                DATA_FIELD.FIELD_TIME: parse_normal_date_str(index.strftime("%Y-%m-%d %H:%M:%S")),
                DATA_FIELD.FIELD_OPEN: str2float(row["Open"]),
                DATA_FIELD.FIELD_HIGH: str2float(row["High"]),
                DATA_FIELD.FIELD_LOW: str2float(row["Low"]),
                DATA_FIELD.FIELD_CLOSE: str2float(row["Close"]),
                DATA_FIELD.FIELD_VOLUME: str2float(row["Volume"])
            }

            yield data_dict, False


    def __convert_period_type(self):
        _dict = {
            KL_TYPE.K_DAY: '1d',
            KL_TYPE.K_WEEK: '1wk',
            KL_TYPE.K_MON: '1mo',
            KL_TYPE.K_1M: '1m',
            KL_TYPE.K_5M: '5m',
            KL_TYPE.K_15M: '15m',
            KL_TYPE.K_30M: '30m',
            KL_TYPE.K_60M: '60m',
        }
        return _dict[self.k_type]
