from data_process.common.chan_exception import ChanException, ErrCode


class CombineItem:
    def __init__(self, item):
        from data_process.bi.bi import Bi
        from data_process.kline.kline_unit import Kline_Unit
        from data_process.seg.seg import Seg
        if type(item) == Bi:
            self.time_begin = item.begin_klc.idx
            self.time_end = item.end_klc.idx
            self.high = item._high()
            self.low = item._low()
        elif type(item) == Kline_Unit:
            self.time_begin = item.time
            self.time_end = item.time
            self.high = item.high
            self.low = item.low
        elif type(item) == Seg:
            self.time_begin = item.begin_bi.begin_klc.idx
            self.time_end = item.end_bi.end_klc.idx
            self.high = item._high()
            self.low = item._low()
        else:
            raise ChanException(f"{type(item)} is unsupport sub class of CCombine_Item", ErrCode.COMMON_ERROR)
