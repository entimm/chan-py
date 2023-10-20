from typing import Dict, Optional

from data_process.common.cenum import TrendType
from common.const import DataField
from data_process.common.chan_exception import ChanException, ErrCode
from common.time import Time
from data_process.calculate.boll import BollMetric, BollModel
from data_process.calculate.demark import DemarkEngine, DemarkIndex
from data_process.calculate.kdj import Kdj
from data_process.calculate.macd import Macd, MacdItem
from data_process.calculate.rsi import Rsi
from data_process.calculate.trend_model import TrendModel

from .trade_info import TradeInfo


class Kline_Unit:
    def __init__(self, kl_dict, autofix=False):
        # _time, _close, _open, _high, _low, _extra_info={}
        self.kl_type = None
        self.time: Time = kl_dict[DataField.FIELD_TIME]
        self.close = kl_dict[DataField.FIELD_CLOSE]
        self.open = kl_dict[DataField.FIELD_OPEN]
        self.high = kl_dict[DataField.FIELD_HIGH]
        self.low = kl_dict[DataField.FIELD_LOW]

        self.check(autofix)

        self.trade_info = TradeInfo(kl_dict)

        self.demark: DemarkIndex = DemarkIndex()

        self.sub_kl_list = []  # 次级别KLU列表
        self.sup_kl: Optional[Kline_Unit] = None  # 指向更高级别KLU

        from data_process.kline.kline import Kline
        self.__klc: Optional[Kline] = None  # 指向Kline

        # self.macd: Optional[CMACD_item] = None
        # self.boll: Optional[BOLL_Metric] = None
        self.trend: Dict[TrendType, Dict[int, float]] = {}  # int -> float

        self.limit_flag = 0  # 0:普通 -1:跌停，1:涨停

        self.set_idx(-1)

    @property
    def klc(self):
        assert self.__klc is not None
        return self.__klc

    def set_klc(self, klc):
        self.__klc = klc

    @property
    def idx(self):
        return self.__idx

    def set_idx(self, idx):
        self.__idx: int = idx

    def __str__(self):
        return f"{self.idx}:{self.time}/{self.kl_type} open={self.open} close={self.close} high={self.high} low={self.low} {self.trade_info}"

    def check(self, autofix=False):
        if self.low > min([self.low, self.open, self.high, self.close]):
            if autofix:
                self.low = min([self.low, self.open, self.high, self.close])
            else:
                raise ChanException(f"{self.time} low price={self.low} is not min of [low={self.low}, open={self.open}, high={self.high}, close={self.close}]", ErrCode.KL_DATA_INVALID)
        if self.high < max([self.low, self.open, self.high, self.close]):
            if autofix:
                self.high = max([self.low, self.open, self.high, self.close])
            else:
                raise ChanException(f"{self.time} high price={self.high} is not max of [low={self.low}, open={self.open}, high={self.high}, close={self.close}]", ErrCode.KL_DATA_INVALID)

    def add_children(self, child):
        self.sub_kl_list.append(child)

    def set_parent(self, parent: 'Kline_Unit'):
        self.sup_kl = parent

    def get_children(self):
        yield from self.sub_kl_list

    def _low(self):
        return self.low

    def _high(self):
        return self.high

    def set_metric(self, metric_model_lst: list) -> None:
        for metric_model in metric_model_lst:
            if isinstance(metric_model, Macd):
                self.macd: MacdItem = metric_model.add(self.close)
            elif isinstance(metric_model, TrendModel):
                if metric_model.type not in self.trend:
                    self.trend[metric_model.type] = {}
                self.trend[metric_model.type][metric_model.T] = metric_model.add(self.close)
            elif isinstance(metric_model, BollModel):
                self.boll: BollMetric = metric_model.add(self.close)
            elif isinstance(metric_model, DemarkEngine):
                self.demark = metric_model.update(idx=self.idx, close=self.close, high=self.high, low=self.low)
            elif isinstance(metric_model, Rsi):
                self.rsi = metric_model.add(self.close)
            elif isinstance(metric_model, Kdj):
                self.kdj = metric_model.add(self.high, self.low, self.close)

    def get_parent_klc(self):
        assert self.sup_kl is not None
        return self.sup_kl.klc
