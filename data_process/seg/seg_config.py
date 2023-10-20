from data_process.common.cenum import LeftSegMethod
from data_process.common.chan_exception import ChanException, ErrCode

"""
- seg_algo：线段计算方法
  - chan：利用特征序列来计算（默认）
  - 1+1：都业华版本 1+1 终结算法
  - break：线段破坏定义来计算线段
- left_seg_method: 剩余那些不能归入确定线段的笔如何处理成段
  - all：收集至最后一个方向正确的笔，成为一段
  - peak：如果有个靠谱的新的极值，那么分成两段（默认）
"""


class SegConfig:
    def __init__(self, seg_algo="chan", left_method="peak"):
        self.seg_algo = seg_algo
        if left_method == "all":
            self.left_method = LeftSegMethod.ALL
        elif left_method == "peak":
            self.left_method = LeftSegMethod.PEAK
        else:
            raise ChanException(f"unknown left_seg_method={left_method}", ErrCode.PARA_ERROR)
