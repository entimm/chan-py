import copy
from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict

from data_process.common.cenum import BiDir


@dataclass
class Kl:
    idx: int
    close: float
    high: float
    low: float

    def v(self, is_close: bool, _dir: BiDir) -> float:
        if is_close:
            return self.close
        return self.high if _dir == BiDir.UP else self.low


T_DEMARK_TYPE = Literal['setup', 'countdown']


class TDemarkIndex(TypedDict):
    type: T_DEMARK_TYPE
    dir: BiDir
    idx: int
    series: 'DemarkSetup'


class DemarkIndex:
    def __init__(self):
        self.data: List[TDemarkIndex] = []

    def add(self, _dir: BiDir, _type: T_DEMARK_TYPE, idx: int, series: 'DemarkSetup'):
        self.data.append({"dir": _dir, "idx": idx, "type": _type, "series": series})

    def get_setup(self) -> List[TDemarkIndex]:
        return [info for info in self.data if info['type'] == 'setup']

    def get_countdown(self) -> List[TDemarkIndex]:
        return [info for info in self.data if info['type'] == 'countdown']

    def update(self, demark_index: 'DemarkIndex'):
        self.data.extend(demark_index.data)


class DemarkCountdown:
    def __init__(self, _dir: BiDir, kl_list: List[Kl], TDST_peak: float):
        self.dir = _dir
        self.kl_list: List[Kl] = copy.deepcopy(kl_list)
        self.idx = 0
        self.TDST_peak = TDST_peak
        self.finish = False

    def update(self, kl: Kl) -> bool:
        if self.finish:
            return False
        self.kl_list.append(kl)
        if len(self.kl_list) <= DemarkEngine.COUNTDOWN_BIAS:
            return False
        if self.idx == DemarkEngine.MAX_COUNTDOWN:
            self.finish = True
            return False
        if (self.dir == BiDir.DOWN and kl.high > self.TDST_peak) or (self.dir == BiDir.UP and kl.low < self.TDST_peak):
            self.finish = True
            return False
        if self.dir == BiDir.DOWN and self.kl_list[-1].close < self.kl_list[-1 - DemarkEngine.COUNTDOWN_BIAS].v(DemarkEngine.COUNTDOWN_CMP2CLOSE, self.dir):
            self.idx += 1
            return True
        if self.dir == BiDir.UP and self.kl_list[-1].close > self.kl_list[-1 - DemarkEngine.COUNTDOWN_BIAS].v(DemarkEngine.COUNTDOWN_CMP2CLOSE, self.dir):
            self.idx += 1
            return True
        return False


class DemarkSetup:
    def __init__(self, _dir: BiDir, kl_list: List[Kl], pre_kl: Kl):
        self.dir = _dir
        self.kl_list: List[Kl] = copy.deepcopy(kl_list)
        self.pre_kl = pre_kl  # 跳空时用
        assert len(self.kl_list) == DemarkEngine.SETUP_BIAS
        self.countdown: Optional[DemarkCountdown] = None
        self.setup_finished = False
        self.idx = 0
        self.TDST_peak: Optional[float] = None

        self.last_demark_index = DemarkIndex()  # 缓存用

    def update(self, kl: Kl) -> DemarkIndex:
        self.last_demark_index = DemarkIndex()
        if not self.setup_finished:
            self.kl_list.append(kl)
            if self.dir == BiDir.DOWN:
                if self.kl_list[-1].close < self.kl_list[-1 - DemarkEngine.SETUP_BIAS].v(DemarkEngine.SETUP_CMP2CLOSE, self.dir):
                    self.add_setup()
                else:
                    self.setup_finished = True
            elif self.kl_list[-1].close > self.kl_list[-1 - DemarkEngine.SETUP_BIAS].v(DemarkEngine.SETUP_CMP2CLOSE, self.dir):
                self.add_setup()
            else:
                self.setup_finished = True
        if self.idx == DemarkEngine.DEMARK_LEN and not self.setup_finished and self.countdown is None:
            self.countdown = DemarkCountdown(self.dir, self.kl_list[:-1], self.cal_tdst_peak())
        if self.countdown is not None and self.countdown.update(kl):
            self.last_demark_index.add(self.dir, 'countdown', self.countdown.idx, self)
        return self.last_demark_index

    def add_setup(self):
        self.idx += 1
        self.last_demark_index.add(self.dir, 'setup', self.idx, self)

    def cal_tdst_peak(self) -> float:
        assert len(self.kl_list) == DemarkEngine.SETUP_BIAS + DemarkEngine.DEMARK_LEN
        arr = self.kl_list[DemarkEngine.SETUP_BIAS:DemarkEngine.SETUP_BIAS + DemarkEngine.DEMARK_LEN]
        assert len(arr) == DemarkEngine.DEMARK_LEN
        if self.dir == BiDir.DOWN:
            res = max(kl.high for kl in arr)
            if DemarkEngine.TIAOKONG_ST and arr[0].high < self.pre_kl.close:
                res = max(res, self.pre_kl.close)
        else:
            res = min(kl.low for kl in arr)
            if DemarkEngine.TIAOKONG_ST and arr[0].low > self.pre_kl.close:
                res = min(res, self.pre_kl.close)
        self.TDST_peak = res
        return res


class DemarkEngine:
    DEMARK_LEN = 9
    SETUP_BIAS = 4
    COUNTDOWN_BIAS = 2
    MAX_COUNTDOWN = 13
    TIAOKONG_ST = True  # 第一根跳空时是否跟前一根的close比
    SETUP_CMP2CLOSE = True
    COUNTDOWN_CMP2CLOSE = True

    def __init__(
        self,
        demark_len=9,
        setup_bias=4,
        countdown_bias=2,
        max_countdown=13,
        tiaokong_st=True,
        setup_cmp2close=True,
        countdown_cmp2close=True
    ):
        DemarkEngine.DEMARK_LEN = demark_len
        DemarkEngine.SETUP_BIAS = setup_bias
        DemarkEngine.COUNTDOWN_BIAS = countdown_bias
        DemarkEngine.MAX_COUNTDOWN = max_countdown
        DemarkEngine.TIAOKONG_ST = tiaokong_st
        DemarkEngine.SETUP_CMP2CLOSE = setup_cmp2close
        DemarkEngine.COUNTDOWN_CMP2CLOSE = countdown_cmp2close

        self.kl_lst: List[Kl] = []
        self.series: List[DemarkSetup] = []

    def update(self, idx: int, close: float, high: float, low: float) -> DemarkIndex:
        self.kl_lst.append(Kl(idx, close, high, low))
        if len(self.kl_lst) <= DemarkEngine.SETUP_BIAS+1:
            return DemarkIndex()

        if self.kl_lst[-1].close < self.kl_lst[-1-self.SETUP_BIAS].close:
            if not any(series.dir == BiDir.DOWN and not series.setup_finished for series in self.series):
                self.series.append(DemarkSetup(BiDir.DOWN, self.kl_lst[-DemarkEngine.SETUP_BIAS - 1:-1], self.kl_lst[-DemarkEngine.SETUP_BIAS - 2]))
            for series in self.series:
                if series.dir == BiDir.UP and series.countdown is None and not series.setup_finished:
                    series.setup_finished = True
        elif self.kl_lst[-1].close > self.kl_lst[-1-self.SETUP_BIAS].close:
            if not any(series.dir == BiDir.UP and not series.setup_finished for series in self.series):
                self.series.append(DemarkSetup(BiDir.UP, self.kl_lst[-DemarkEngine.SETUP_BIAS - 1:-1], self.kl_lst[-DemarkEngine.SETUP_BIAS - 2]))
            for series in self.series:
                if series.dir == BiDir.DOWN and series.countdown is None and not series.setup_finished:
                    series.setup_finished = True

        self.clear()
        self.clean_series_from_setup_finish()

        result = self.cal_result()
        self.clear()
        return result

    def cal_result(self) -> DemarkIndex:
        demark_index = DemarkIndex()
        for series in self.series:
            demark_index.update(series.last_demark_index)
        return demark_index

    def clear(self):
        invalid_series = [series for series in self.series if series.setup_finished and series.countdown is None]
        for s in invalid_series:
            self.series.remove(s)
        invalid_series = [series for series in self.series if series.countdown is not None and series.countdown.finish]
        for s in invalid_series:
            self.series.remove(s)

    def clean_series_from_setup_finish(self):
        finished_setup: Optional[int] = None
        for series in self.series:
            demark_idx = series.update(self.kl_lst[-1])
            for setup_idx in demark_idx.get_setup():
                if setup_idx['idx'] == DemarkEngine.DEMARK_LEN:
                    assert finished_setup is None
                    finished_setup = id(series)
        if finished_setup is not None:
            self.series = [series for series in self.series if id(series) == finished_setup]
