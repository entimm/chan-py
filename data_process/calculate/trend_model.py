from data_process.common.cenum import TrendType
from data_process.common.chan_exception import ChanException, ErrCode


class TrendModel:
    def __init__(self, trend_type: TrendType, T: int):
        self.T = T
        self.arr = []
        self.type = trend_type

    def add(self, value) -> float:
        self.arr.append(value)
        if len(self.arr) > self.T:
            self.arr = self.arr[-self.T:]
        if self.type == TrendType.MEAN:
            return sum(self.arr)/len(self.arr)
        elif self.type == TrendType.MAX:
            return max(self.arr)
        elif self.type == TrendType.MIN:
            return min(self.arr)
        else:
            raise ChanException(f"Unknown trendModel Type = {self.type}", ErrCode.PARA_ERROR)
