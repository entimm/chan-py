from data_process.bi.bi import Bi
from data_process.combiner.kline_combiner import KlineCombiner
from data_process.common.cenum import BiDir, FxType


class Eigen(KlineCombiner[Bi]):
    def __init__(self, bi, _dir):
        super(Eigen, self).__init__(bi, _dir)
        self.gap = False

    def update_fx(self, _pre: 'Eigen', _next: 'Eigen', exclude_included=False, allow_hl_equal=None):
        """
        更新分型，检测是否有跳空缺口
        """
        super(Eigen, self).update_fx(_pre, _next, exclude_included, allow_hl_equal)

        if (self.fx == FxType.TOP and _pre.high < self.low) or \
           (self.fx == FxType.BOTTOM and _pre.low > self.high):
            self.gap = True

    def __str__(self):
        return f"{self.lst[0].idx}~{self.lst[-1].idx} gap={self.gap} fx={self.fx}"

    def get_peak_bi_idx(self):
        assert self.fx != FxType.UNKNOWN
        bi_dir = self.lst[0].dir
        if bi_dir == BiDir.UP:  # 下降线段
            return self.get_peak_klu(is_high=False).idx-1
        else:
            return self.get_peak_klu(is_high=True).idx-1
