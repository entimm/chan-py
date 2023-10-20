import baostock as bs

from common.const import AuType, DataField, LvType
from common.func_util import create_item_dict
from common.func_util import kl_type_lt_day
from data_fetch.abs_stock_api import AbsStockApi


class BaoStockFetcher(AbsStockApi):
    is_connect = None

    def __init__(self, code, k_type=LvType.K_DAY, begin_date=None, end_date=None, autype=AuType.QFQ):
        super(BaoStockFetcher, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        # 天级别以上才有详细交易信息
        if kl_type_lt_day(self.k_type):
            if not self.is_stock:
                raise Exception("没有获取到数据，注意指数是没有分钟级别数据的！")
            fields = "time,open,high,low,close"
        else:
            fields = "date,open,high,low,close,volume,amount,turn"
        autype_dict = {AuType.QFQ: "2", AuType.HFQ: "1", AuType.NONE: "3"}
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
            yield create_item_dict(rs.get_row_data(), self.column_name_map(fields)), False

    def set_base_info(self):
        rs = bs.query_stock_basic(code=self.code)
        if rs.error_code != '0':
            raise Exception(rs.error_msg)
        code, code_name, ipoDate, outDate, stock_type, status = rs.get_row_data()
        self.name = code_name
        self.is_stock = (stock_type == '1')

    def __convert_period_type(self):
        _dict = {
            LvType.K_DAY: 'd',
            LvType.K_WEEK: 'w',
            LvType.K_MON: 'm',
            LvType.K_5M: '5',
            LvType.K_15M: '15',
            LvType.K_30M: '30',
            LvType.K_60M: '60',
        }
        return _dict[self.k_type]

    def column_name_map(self, fileds: str):
        _dict = {
            "time": DataField.FIELD_TIME,
            "date": DataField.FIELD_TIME,
            "open": DataField.FIELD_OPEN,
            "high": DataField.FIELD_HIGH,
            "low": DataField.FIELD_LOW,
            "close": DataField.FIELD_CLOSE,
            "volume": DataField.FIELD_VOLUME,
            "amount": DataField.FIELD_TURNOVER,
            "turn": DataField.FIELD_TURNRATE,
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
