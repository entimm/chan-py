import baostock as bs

from common.const import AUTYPE, DATA_FIELD, KL_TYPE
from common.func_util import create_item_dict
from common.func_util import kltype_lt_day
from data_fetch.abs_stock_api import AbsStockApi


class BaoStockFetcher(AbsStockApi):
    is_connect = None

    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=AUTYPE.QFQ):
        super(BaoStockFetcher, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        # 天级别以上才有详细交易信息
        if kltype_lt_day(self.k_type):
            if not self.is_stock:
                raise Exception("没有获取到数据，注意指数是没有分钟级别数据的！")
            fields = "time,open,high,low,close"
        else:
            fields = "date,open,high,low,close,volume,amount,turn"
        autype_dict = {AUTYPE.QFQ: "2", AUTYPE.HFQ: "1", AUTYPE.NONE: "3"}
        rs = bs.query_history_k_data_plus(
            code=self.code,
            fields=fields,
            start_date=self.begin_date,
            end_date=self.end_date,
            frequency=self.__convert_period_type(),
            adjustflag=autype_dict[self.autype],
        )
        if rs.error_code != '0':
            raise Exception(rs.error_msg)
        while rs.error_code == '0' and rs.next():
            yield create_item_dict(rs.get_row_data(), self.columnNameMap(fields)), False

    def SetBasciInfo(self):
        rs = bs.query_stock_basic(code=self.code)
        if rs.error_code != '0':
            raise Exception(rs.error_msg)
        code, code_name, ipoDate, outDate, stock_type, status = rs.get_row_data()
        self.name = code_name
        self.is_stock = (stock_type == '1')

    def __convert_period_type(self):
        _dict = {
            KL_TYPE.K_DAY: 'd',
            KL_TYPE.K_WEEK: 'w',
            KL_TYPE.K_MON: 'm',
            KL_TYPE.K_5M: '5',
            KL_TYPE.K_15M: '15',
            KL_TYPE.K_30M: '30',
            KL_TYPE.K_60M: '60',
        }
        return _dict[self.k_type]

    def columnNameMap(self, fileds: str):
        _dict = {
            "time": DATA_FIELD.FIELD_TIME,
            "date": DATA_FIELD.FIELD_TIME,
            "open": DATA_FIELD.FIELD_OPEN,
            "high": DATA_FIELD.FIELD_HIGH,
            "low": DATA_FIELD.FIELD_LOW,
            "close": DATA_FIELD.FIELD_CLOSE,
            "volume": DATA_FIELD.FIELD_VOLUME,
            "amount": DATA_FIELD.FIELD_TURNOVER,
            "turn": DATA_FIELD.FIELD_TURNRATE,
        }
        return [_dict[x] for x in fileds.split(",")]

    @classmethod
    def do_init(cls):
        if not cls.is_connect:
            cls.is_connect = bs.login()

    @classmethod
    def do_close(cls):
        if cls.is_connect:
            bs.logout()
            cls.is_connect = None
