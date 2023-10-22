from typing import List


class MacdItem:
    def __init__(self, fast_ema, slow_ema, DIF, DEA):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.DIF = DIF
        self.DEA = DEA
        self.macd = 2 * (DIF - DEA)


class Macd:
    def __init__(self, fastperiod=12, slowperiod=26, signalperiod=9):
        self.macd_info: List[MacdItem] = []
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod

    def add(self, value) -> MacdItem:
        if not self.macd_info:
            self.macd_info.append(MacdItem(fast_ema=value, slow_ema=value, DIF=0, DEA=0))
        else:
            _fast_ema = (2 * value + (self.fastperiod - 1) * self.macd_info[-1].fast_ema) / (self.fastperiod + 1)
            _slow_ema = (2 * value + (self.slowperiod - 1) * self.macd_info[-1].slow_ema) / (self.slowperiod + 1)
            _dif = _fast_ema - _slow_ema
            _dea = (2 * _dif + (self.signalperiod - 1) * self.macd_info[-1].DEA) / (self.signalperiod + 1)
            self.macd_info.append(MacdItem(fast_ema=_fast_ema, slow_ema=_slow_ema, DIF=_dif, DEA=_dea))
        return self.macd_info[-1]
