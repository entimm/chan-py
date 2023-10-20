from .cenum import BiDir
from common.const import LvType




def kl_type_lte_day(_type):
    return _type in [LvType.K_1M, LvType.K_5M, LvType.K_15M, LvType.K_30M, LvType.K_60M, LvType.K_DAY]


def check_kl_type_order(type_list: list):
    _dict = {
        LvType.K_1M: 1,
        LvType.K_3M: 2,
        LvType.K_5M: 3,
        LvType.K_15M: 4,
        LvType.K_30M: 5,
        LvType.K_60M: 6,
        LvType.K_DAY: 7,
        LvType.K_WEEK: 8,
        LvType.K_MON: 9,
        LvType.K_QUARTER: 10,
        LvType.K_YEAR: 11,
    }
    last_lv = float("inf")
    for kl_type in type_list:
        cur_lv = _dict[kl_type]
        assert cur_lv < last_lv, "lv_list的顺序必须从大级别到小级别"
        last_lv = cur_lv


def revert_bi_dir(dir):
    return BiDir.DOWN if dir == BiDir.UP else BiDir.UP


def has_overlap(l1, h1, l2, h2, equal=False):
    return h2 >= l1 and h1 >= l2 if equal else h2 > l1 and h1 > l2


def _parse_inf(v):
    if type(v) == float:
        if v == float("inf"):
            v = 'float("inf")'
        if v == float("-inf"):
            v = 'float("-inf")'
    return v
