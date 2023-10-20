from enum import Enum, auto
from typing import Literal

from common.const import DataField


class KlineDir(Enum):
    UP = auto()
    DOWN = auto()
    COMBINE = auto()
    INCLUDED = auto()


class FxType(Enum):
    BOTTOM = auto()
    TOP = auto()
    UNKNOWN = auto()


class BiDir(Enum):
    UP = auto()
    DOWN = auto()


class BiType(Enum):
    UNKNOWN = auto()
    STRICT = auto()
    SUB_VALUE = auto()  # 次高低点成笔
    TIAOKONG_THRED = auto()
    DAHENG = auto()
    TUIBI = auto()
    UNSTRICT = auto()
    TIAOKONG_VALUE = auto()


BSP_MAIN_TYPE = Literal['1', '2', '3']


class BspType(Enum):
    T1 = '1'
    T1P = '1p'
    T2 = '2'
    T2S = '2s'
    T3A = '3a'  # 中枢在1类后面
    T3B = '3b'  # 中枢在1类前面

    def main_type(self) -> BSP_MAIN_TYPE:
        return self.value[0]  # type: ignore


class TrendType(Enum):
    MEAN = "mean"
    MAX = "max"
    MIN = "min"


class TrendLineSide(Enum):
    INSIDE = auto()
    OUTSIDE = auto()


class LeftSegMethod(Enum):
    ALL = auto()
    PEAK = auto()


class FxCheckMethod(Enum):
    STRICT = auto()
    LOSS = auto()
    HALF = auto()
    TOTALLY = auto()


class SegType(Enum):
    BI = auto()
    SEG = auto()


class MacdAlgo(Enum):
    AREA = auto()
    PEAK = auto()
    FULL_AREA = auto()
    DIFF = auto()
    SLOPE = auto()
    AMP = auto()
    VOLUMN = auto()
    AMOUNT = auto()
    VOLUMN_AVG = auto()
    AMOUNT_AVG = auto()
    TURNRATE_AVG = auto()
    RSI = auto()


TRADE_INFO_LST = [DataField.FIELD_VOLUME, DataField.FIELD_TURNOVER, DataField.FIELD_TURNRATE]
