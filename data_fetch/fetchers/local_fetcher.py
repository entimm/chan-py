import pandas as pd

from common.const import AUTYPE, DATA_FIELD, KL_TYPE
from common.func_util import parse_normal_date_str, str2float
from data_fetch.abs_stock_api import AbsStockApi


class LocalFetcher(AbsStockApi):
    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=AUTYPE.QFQ):
        super(LocalFetcher, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):

        file_path = "data/_local.csv"
        df = pd.read_csv(file_path)

        for index, row in df.iterrows():
            data_dict = {
                DATA_FIELD.FIELD_TIME: parse_normal_date_str(row["Date"]),
                DATA_FIELD.FIELD_OPEN: str2float(row["Open"]),
                DATA_FIELD.FIELD_HIGH: str2float(row["High"]),
                DATA_FIELD.FIELD_LOW: str2float(row["Low"]),
                DATA_FIELD.FIELD_CLOSE: str2float(row["Close"]),
                DATA_FIELD.FIELD_VOLUME: str2float(row["Volume"])
            }

            yield data_dict, False