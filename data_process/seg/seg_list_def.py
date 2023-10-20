from data_process.bi.bi_list import CBiList
from data_process.common.cenum import SEG_TYPE

from .seg_config import CSegConfig
from .seg_list_comm import CSegListComm


def is_up_seg(bi, pre_bi):
    """
    判断给定的笔是否是上升线段
    """
    return bi._high() > pre_bi._high()


def is_down_seg(bi, pre_bi):
    """
    判断给定的笔是否是下降线段
    """
    return bi._low() < pre_bi._low()


class CSegListDef(CSegListComm):
    def __init__(self, seg_config=CSegConfig(), lv=SEG_TYPE.BI):
        super(CSegListDef, self).__init__(seg_config=seg_config, lv=lv)
        # `sure_seg_update_end`: 一个标志，表示是否更新确定线段的结束
        self.sure_seg_update_end = False

    def update(self, bi_lst: CBiList):
        self.do_init()
        self.cal_bi_sure(bi_lst)
        self.collect_left_seg(bi_lst)

    def update_last_end(self, bi_lst, new_endbi_idx: int):
        """
        更新最后一个线段的结束笔
        """
        # 首先获取最后一个线段的结束笔的索引
        last_endbi_idx = self[-1].end_bi.idx
        # 确保新的结束笔索引大于等于最后一个线段的结束笔索引加2
        assert new_endbi_idx >= last_endbi_idx + 2
        # 更新最后一个线段的结束笔
        self[-1].end_bi = bi_lst[new_endbi_idx]
        # 更新最后一个线段的笔列表
        self.lst[-1].update_bi_list(bi_lst, last_endbi_idx, new_endbi_idx)

    def cal_bi_sure(self, bi_lst):
        """
        计算确定的线段
        """
        # `peak_bi`是一个峰值笔，用于记录当前的峰值
        peak_bi = None
        if len(bi_lst) == 0:
            return
        # 遍历给定的笔列表，根据笔的方向和最后一个线段的方向，确定是否需要更新峰值笔或添加新的线段
        for idx, bi in enumerate(bi_lst):
            if idx < 2:
                continue
            if peak_bi and ((bi.is_up() and peak_bi.is_up() and bi._high() >= peak_bi._high()) or (bi.is_down() and peak_bi.is_down() and bi._low() <= peak_bi._low())):
                peak_bi = bi
                continue
            if self.sure_seg_update_end and len(self) and bi.dir == self[-1].dir and ((bi.is_up() and bi._high() >= self[-1].end_bi._high()) or (bi.is_down() and bi._low() <= self[-1].end_bi._low())):
                self.update_last_end(bi_lst, bi.idx)
                peak_bi = None
                continue
            pre_bi = bi_lst[idx-2]
            if (bi.is_up() and is_up_seg(bi, pre_bi)) or \
               (bi.is_down() and is_down_seg(bi, pre_bi)):
                if peak_bi is None:
                    if len(self) == 0 or bi.dir != self[-1].dir:
                        peak_bi = bi
                        continue
                elif peak_bi.dir != bi.dir:
                    if bi.idx - peak_bi.idx <= 2:
                        continue
                    self.add_new_seg(bi_lst, peak_bi.idx)
                    peak_bi = bi
                    continue
        if peak_bi is not None:
            self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False)
