from data_process.bi.bi import CBi
from data_process.combiner.kline_combiner import CKLine_Combiner
from data_process.common.cenum import BI_DIR, FX_TYPE


class CEigen(CKLine_Combiner[CBi]):
    def __init__(self, bi, _dir):
        super(CEigen, self).__init__(bi, _dir)
        self.gap = False

    def update_fx(self, _pre: 'CEigen', _next: 'CEigen', exclude_included=False, allow_hl_equal=None):
        """
        更新分型，检测是否有跳空缺口
        """
        super(CEigen, self).update_fx(_pre, _next, exclude_included, allow_hl_equal)

        if (self.fx == FX_TYPE.TOP and _pre.high < self.low) or \
           (self.fx == FX_TYPE.BOTTOM and _pre.low > self.high):
            self.gap = True

    def __str__(self):
        return f"{self.lst[0].idx}~{self.lst[-1].idx} gap={self.gap} fx={self.fx}"

    def GetPeakBiIdx(self):
        assert self.fx != FX_TYPE.UNKNOWN
        bi_dir = self.lst[0].dir
        if bi_dir == BI_DIR.UP:  # 下降线段
            return self.get_peak_klu(is_high=False).idx-1
        else:
            return self.get_peak_klu(is_high=True).idx-1
