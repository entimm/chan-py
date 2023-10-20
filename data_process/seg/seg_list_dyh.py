from data_process.bi.bi_list import CBiList
from data_process.common.cenum import BI_DIR, SEG_TYPE

from .seg_config import CSegConfig
from .seg_list_comm import CSegListComm


def situation1(cur_bi, next_bi, pre_bi):
    """
    用于判断给定的笔是否满足特定的线段确定性条件
    """
    if cur_bi.is_down() and cur_bi._low() > pre_bi._low():
        if next_bi._high() < cur_bi._high() and next_bi._low() < cur_bi._low():
            return True
    elif cur_bi.is_up() and cur_bi._high() < pre_bi._high():
        if next_bi._low() > cur_bi._low() and next_bi._high() > cur_bi._high():
            return True
    return False


def situation2(cur_bi, next_bi, pre_bi):
    """
    用于判断给定的笔是否满足特定的线段确定性条件
    """
    if cur_bi.is_down() and cur_bi._low() < pre_bi._low():
        if next_bi._high() < cur_bi._high() and next_bi._low() < pre_bi._low():
            return True
    elif cur_bi.is_up() and cur_bi._high() > pre_bi._high():
        if next_bi._low() > cur_bi._low() and next_bi._high() > pre_bi._high():
            return True
    return False


class CSegListDYH(CSegListComm):
    def __init__(self, seg_config=CSegConfig(), lv=SEG_TYPE.BI):
        super(CSegListDYH, self).__init__(seg_config=seg_config, lv=lv)
        # `sure_seg_update_end`: 一个标志，表示是否更新确定线段的结束
        self.sure_seg_update_end = False

    def update(self, bi_lst: CBiList):
        self.do_init()
        # 接着调用`cal_bi_sure`方法计算确定的线段
        self.cal_bi_sure(bi_lst)
        # 调用`try_update_last_seg`方法尝试更新最后一个线段
        self.try_update_last_seg(bi_lst)
        # 如果存在左侧笔的突破，调用`cal_bi_unsure`方法
        if self.left_bi_break(bi_lst):
            self.cal_bi_unsure(bi_lst)
        # 收集剩余的线段
        self.collect_left_seg(bi_lst)

    def cal_bi_sure(self, bi_lst):
        """
        计算确定的线段
        """
        BI_LEN = len(bi_lst)
        next_begin_bi = bi_lst[0]
        # 遍历给定的笔列表，根据笔的方向和最后一个线段的方向，确定是否需要更新峰值笔或添加新的线段
        for idx, bi in enumerate(bi_lst):
            if idx + 2 >= BI_LEN or idx < 2:
                continue
            if len(self) > 0 and bi.dir != self[-1].end_bi.dir:
                continue
            if bi.is_down() and bi_lst[idx-1]._high() < next_begin_bi._low():
                continue
            if bi.is_up() and bi_lst[idx-1]._low() > next_begin_bi._high():
                continue
            if self.sure_seg_update_end and len(self) and ((bi.is_down() and bi._low() < self[-1].end_bi._low()) or (bi.is_up() and bi._high() > self[-1].end_bi._high())):
                self[-1].end_bi = bi
                if idx != BI_LEN-1:
                    next_begin_bi = bi_lst[idx+1]
                    continue
            # 使用`situation1`和`situation2`函数来判断线段的确定性
            if (len(self) == 0 or bi.idx - self[-1].end_bi.idx >= 4) and (situation1(bi, bi_lst[idx + 2], bi_lst[idx - 2]) or situation2(bi, bi_lst[idx + 2], bi_lst[idx - 2])):
                self.add_new_seg(bi_lst, idx-1)
                next_begin_bi = bi

    def cal_bi_unsure(self, bi_lst: CBiList):
        """
        计算不确定的线段
        根据最后一个线段的方向和后续的笔，确定是否需要添加新的不确定线段
        """
        if len(self) == 0:
            return
        last_seg_dir = self[-1].end_bi.dir
        end_bi = None
        peak_value = float("inf") if last_seg_dir == BI_DIR.UP else float("-inf")
        for bi in bi_lst[self[-1].end_bi.idx+3:]:
            if bi.dir == last_seg_dir:
                continue
            cur_value = bi._low() if last_seg_dir == BI_DIR.UP else bi._high()
            if (last_seg_dir == BI_DIR.UP and cur_value < peak_value) or \
               (last_seg_dir == BI_DIR.DOWN and cur_value > peak_value):
                end_bi = bi
                peak_value = cur_value
        if end_bi:
            self.add_new_seg(bi_lst, end_bi.idx, is_sure=False)

    def try_update_last_seg(self, bi_lst: CBiList):
        """
        尝试更新最后一个线段
        根据最后一个线段的方向和后续的笔，确定是否需要更新最后一个线段的结束笔
        """
        if len(self) == 0:
            return
        last_bi = self[-1].end_bi
        peak_value = last_bi.get_end_val()
        new_peak_bi = None
        for bi in bi_lst[self[-1].end_bi.idx+1:]:
            if bi.dir != last_bi.dir:
                continue
            if bi.is_down() and bi._low() < peak_value:
                peak_value = bi._low()
                new_peak_bi = bi
            elif bi.is_up() and bi._high() > peak_value:
                peak_value = bi._high()
                new_peak_bi = bi
        if new_peak_bi:
            self[-1].end_bi = new_peak_bi
            self[-1].is_sure = False
