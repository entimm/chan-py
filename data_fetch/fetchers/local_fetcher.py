import pandas as pd

from common.const import AuType, DataField, LvType
from common.func_util import parse_normal_date_str, str2float
from data_fetch.abs_stock_api import AbsStockApi


class LocalFetcher(AbsStockApi):
    def __init__(self, code, k_type=LvType.K_DAY, begin_date=None, end_date=None, autype=AuType.QFQ):
        super(LocalFetcher, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):

        file_path = "data/_local.csv"
        df = pd.read_csv(file_path)

        for index, row in df.tail(10000).iterrows():
            data_dict = {
                DataField.FIELD_TIME: parse_normal_date_str(row["Date"]),
                DataField.FIELD_OPEN: str2float(row["Open"]),
                DataField.FIELD_HIGH: str2float(row["High"]),
                DataField.FIELD_LOW: str2float(row["Low"]),
                DataField.FIELD_CLOSE: str2float(row["Close"]),
                DataField.FIELD_VOLUME: str2float(row["Volume"])
            }

            yield data_dict, False