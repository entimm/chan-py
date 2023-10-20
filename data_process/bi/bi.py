from typing import List, Optional

from common.const import DataField
from data_process.common.cache import MakeCache
from data_process.common.cenum import BiDir, BiType, FxType, MacdAlgo
from data_process.common.chan_exception import ChanException, ErrCode
from data_process.kline.kline import Kline
from data_process.kline.kline_unit import Kline_Unit

class Bi:
    def __init__(self, begin_klc: Kline, end_klc: Kline, idx: int, is_sure: bool):
        # self.__begin_klc = begin_klc
        # self.__end_klc = end_klc
        self.__dir = None
        self.__idx = idx
        self.__type = BiType.STRICT

        self.set(begin_klc, end_klc)

        self.__is_sure = is_sure
        self.__sure_end = None

        self.__klc_lst: List[Kline] = []
        self.__seg_idx: Optional[int] = None

        # 解决循环引用问题
        from data_process.seg.seg import Seg
        from data_process.bsl_point.bs_point import BsPoint

        self.parent_seg: Optional[Seg[Bi]] = None  # 在哪个线段里面
        self.bsp: Optional[BsPoint] = None  # 尾部是不是买卖点

        self.next: Optional[Bi] = None
        self.pre: Optional[Bi] = None

    def clean_cache(self):
        self._memoize_cache = {}

    @property
    def begin_klc(self):
        return self.__begin_klc

    @property
    def end_klc(self):
        return self.__end_klc

    @property
    def dir(self):
        return self.__dir

    @property
    def idx(self):
        return self.__idx

    @property
    def type(self):
        return self.__type

    @property
    def is_sure(self):
        return self.__is_sure

    @property
    def sure_end(self):
        return self.__sure_end

    @property
    def klc_lst(self):
        return self.__klc_lst

    @property
    def seg_idx(self):
        return self.__seg_idx

    def set_seg_idx(self, idx):
        self.__seg_idx = idx

    def __str__(self):
        return f"{self.dir}|{self.begin_klc} ~ {self.end_klc}"

    def check(self):
        try:
            if self.is_down():
                assert self.begin_klc.high > self.end_klc.low
            else:
                assert self.begin_klc.low < self.end_klc.high
        except Exception as e:
            raise ChanException(
                f"{self.idx}:{self.begin_klc[0].time}~{self.end_klc[-1].time}笔的方向和收尾位置不一致!",
                ErrCode.BI_ERR) from e

    def set(self, begin_klc: Kline, end_klc: Kline):
        self.__begin_klc: Kline = begin_klc
        self.__end_klc: Kline = end_klc
        if begin_klc.fx == FxType.BOTTOM:
            self.__dir = BiDir.UP
        elif begin_klc.fx == FxType.TOP:
            self.__dir = BiDir.DOWN
        else:
            raise ChanException("ERROR DIRECTION when creating bi", ErrCode.BI_ERR)
        self.check()
        self.clean_cache()

    @MakeCache
    def get_begin_val(self):
        return self.begin_klc.low if self.is_up() else self.begin_klc.high

    @MakeCache
    def get_end_val(self):
        return self.end_klc.high if self.is_up() else self.end_klc.low

    @MakeCache
    def get_begin_klu(self) -> Kline_Unit:
        if self.is_up():
            return self.begin_klc.get_peak_klu(is_high=False)
        else:
            return self.begin_klc.get_peak_klu(is_high=True)

    @MakeCache
    def get_end_klu(self) -> Kline_Unit:
        if self.is_up():
            return self.end_klc.get_peak_klu(is_high=True)
        else:
            return self.end_klc.get_peak_klu(is_high=False)

    @MakeCache
    def amp(self):
        return abs(self.get_end_val() - self.get_begin_val())

    @MakeCache
    def get_klu_cnt(self):
        return self.get_end_klu().idx - self.get_begin_klu().idx + 1

    @MakeCache
    def get_klc_cnt(self):
        assert self.end_klc.idx == self.get_end_klu().klc.idx
        assert self.begin_klc.idx == self.get_begin_klu().klc.idx
        return self.end_klc.idx - self.begin_klc.idx + 1

    @MakeCache
    def _high(self):
        return self.end_klc.high if self.is_up() else self.begin_klc.high

    @MakeCache
    def _low(self):
        return self.begin_klc.low if self.is_up() else self.end_klc.low

    @MakeCache
    def _mid(self):
        return (self._high() + self._low()) / 2  # 笔的中位价

    @MakeCache
    def is_down(self):
        return self.dir == BiDir.DOWN

    @MakeCache
    def is_up(self):
        return self.dir == BiDir.UP

    def update_virtual_end(self, new_klc: Kline):
        self.__sure_end = self.end_klc
        self.update_new_end(new_klc)
        self.__is_sure = False
        self.clean_cache()

    def restore_from_virtual_end(self):
        self.__is_sure = True
        assert self.sure_end is not None
        self.update_new_end(new_klc=self.sure_end)
        self.__sure_end = None
        self.clean_cache()

    def is_virtual_end(self):
        return self.sure_end is not None

    def update_new_end(self, new_klc: Kline):
        self.__end_klc = new_klc
        self.check()
        self.clean_cache()

    def cal_macd_metric(self, macd_algo, is_reverse):
        if macd_algo == MacdAlgo.AREA:
            return self.cal_macd_half(is_reverse)
        elif macd_algo == MacdAlgo.PEAK:
            return self.cal_macd_peak()
        elif macd_algo == MacdAlgo.FULL_AREA:
            return self.cal_macd_area()
        elif macd_algo == MacdAlgo.DIFF:
            return self.cal_macd_diff()
        elif macd_algo == MacdAlgo.SLOPE:
            return self.cal_macd_slope()
        elif macd_algo == MacdAlgo.AMP:
            return self.cal_macd_amp()
        elif macd_algo == MacdAlgo.AMOUNT:
            return self.cal_macd_trade_metric(DataField.FIELD_TURNOVER, cal_avg=False)
        elif macd_algo == MacdAlgo.VOLUMN:
            return self.cal_macd_trade_metric(DataField.FIELD_VOLUME, cal_avg=False)
        elif macd_algo == MacdAlgo.VOLUMN_AVG:
            return self.cal_macd_trade_metric(DataField.FIELD_VOLUME, cal_avg=True)
        elif macd_algo == MacdAlgo.AMOUNT_AVG:
            return self.cal_macd_trade_metric(DataField.FIELD_TURNOVER, cal_avg=True)
        elif macd_algo == MacdAlgo.TURNRATE_AVG:
            return self.cal_macd_trade_metric(DataField.FIELD_TURNRATE, cal_avg=True)
        elif macd_algo == MacdAlgo.RSI:
            return self.cal_rsi()
        else:
            raise ChanException(
                f"unsupport macd_algo={macd_algo}, should be one of area/full_area/peak/diff/slope/amp",
                ErrCode.PARA_ERROR)

    @MakeCache
    def cal_rsi(self):
        rsi_lst: List[float] = []
        for klc in self.klc_lst:
            rsi_lst.extend(klu.rsi for klu in klc.lst)
        return 10000.0 / (min(rsi_lst) + 1e-7) if self.is_down() else max(rsi_lst)

    @MakeCache
    def cal_macd_area(self):
        _s = 1e-7
        for klc in self.klc_lst:
            for klu in klc.lst:
                _s += abs(klu.macd.macd)
        return _s

    @MakeCache
    def cal_macd_peak(self):
        peak = 1e-7
        for klc in self.klc_lst:
            for klu in klc.lst:
                if abs(klu.macd.macd) > peak:
                    if self.is_down() and klu.macd.macd < 0:
                        peak = abs(klu.macd.macd)
                    elif self.is_up() and klu.macd.macd > 0:
                        peak = abs(klu.macd.macd)
        return peak

    def cal_macd_half(self, is_reverse):
        if is_reverse:
            return self.cal_macd_half_reverse()
        else:
            return self.cal_macd_half_obverse()

    @MakeCache
    def cal_macd_half_obverse(self):
        _s = 1e-7
        begin_klu = self.get_begin_klu()
        peak_macd = begin_klu.macd.macd
        for klc in self.klc_lst:
            for klu in klc.lst:
                if klu.idx < begin_klu.idx:
                    continue
                if klu.macd.macd * peak_macd > 0:
                    _s += abs(klu.macd.macd)
                else:
                    break
            else:  # 没有被break，继续找写一个KLC
                continue
            break
        return _s

    @MakeCache
    def cal_macd_half_reverse(self):
        _s = 1e-7
        begin_klu = self.get_end_klu()
        peak_macd = begin_klu.macd.macd
        for klc in self.klc_lst[::-1]:
            for klu in klc[::-1]:
                if klu.idx > begin_klu.idx:
                    continue
                if klu.macd.macd * peak_macd > 0:
                    _s += abs(klu.macd.macd)
                else:
                    break
            else:  # 没有被break，继续找写一个KLC
                continue
            break
        return _s

    @MakeCache
    def cal_macd_diff(self):
        """
        macd红绿柱最大值最小值之差
        """
        _max, _min = float("-inf"), float("inf")
        for klc in self.klc_lst:
            for klu in klc.lst:
                macd = klu.macd.macd
                if macd > _max:
                    _max = macd
                if macd < _min:
                    _min = macd
        return _max - _min

    @MakeCache
    def cal_macd_slope(self):
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_up():
            return (end_klu.high - begin_klu.low) / end_klu.high / (end_klu.idx - begin_klu.idx + 1)
        else:
            return (begin_klu.high - end_klu.low) / begin_klu.high / (end_klu.idx - begin_klu.idx + 1)

    @MakeCache
    def cal_macd_amp(self):
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_down():
            return (begin_klu.high - end_klu.low) / begin_klu.high
        else:
            return (end_klu.high - begin_klu.low) / begin_klu.low

    def cal_macd_trade_metric(self, metric: str, cal_avg=False) -> float:
        _s = 0
        for klc in self.klc_lst:
            for klu in klc.lst:
                metric_res = klu.trade_info.metric[metric]
                if metric_res is None:
                    return 0.0
                _s += metric_res
        return _s / self.get_klu_cnt() if cal_avg else _s

    def set_klc_lst(self, lst):
        self.__klc_lst = lst
