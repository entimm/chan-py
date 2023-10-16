from enum import Enum, auto


class AUTYPE(Enum):
    QFQ = auto()
    HFQ = auto()
    NONE = auto()


class DATA_FIELD:
    FIELD_TIME = "time_key"
    FIELD_OPEN = "open"
    FIELD_HIGH = "high"
    FIELD_LOW = "low"
    FIELD_CLOSE = "close"
    FIELD_VOLUME = "volume"  # 成交量
    FIELD_TURNOVER = "turnover"  # 成交额
    FIELD_TURNRATE = "turnover_rate"  # 换手率


class KL_TYPE(Enum):
    K_1M = auto()
    K_DAY = auto()
    K_WEEK = auto()
    K_MON = auto()
    K_YEAR = auto()
    K_5M = auto()
    K_15M = auto()
    K_30M = auto()
    K_60M = auto()
    K_3M = auto()
    K_QUARTER = auto()
