import abc
from typing import Generic, List, TypeVar, Union, overload

from data_process.bi.bi import Bi
from data_process.bi.bi_list import BiList
from data_process.common.cenum import BiDir, LeftSegMethod, SegType
from data_process.common.chan_exception import ChanException, ErrCode

from .seg import Seg
from .seg_config import SegConfig

SUB_LINE_TYPE = TypeVar('SUB_LINE_TYPE', Bi, "CSeg")


class SegListComm(Generic[SUB_LINE_TYPE]):
    def __init__(self, seg_config=SegConfig(), lv=SegType.BI):
        self.lst: List[Seg[SUB_LINE_TYPE]] = []
        self.lv = lv
        self.do_init()
        self.config = seg_config

    def do_init(self):
        self.lst = []

    def __iter__(self):
        yield from self.lst

    @overload
    def __getitem__(self, index: int) -> Seg[SUB_LINE_TYPE]: ...

    @overload
    def __getitem__(self, index: slice) -> List[Seg[SUB_LINE_TYPE]]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[Seg[SUB_LINE_TYPE]], Seg[SUB_LINE_TYPE]]:
        return self.lst[index]

    def __len__(self):
        return len(self.lst)

    def left_bi_break(self, bi_lst: BiList):
        """
        检查最后一个确定线段之后的笔是否突破了该线段的最后一笔
        """
        if len(self) == 0:
            return False
        last_seg_end_bi = self[-1].end_bi
        for bi in bi_lst[last_seg_end_bi.idx+1:]:
            if last_seg_end_bi.is_up() and bi._high() > last_seg_end_bi._high():
                return True
            elif last_seg_end_bi.is_down() and bi._low() < last_seg_end_bi._low():
                return True
        return False

    def collect_first_seg(self, bi_lst: BiList):
        """
        收集第一个线段。根据配置的方法（峰值或全部），确定如何收集
        """
        if len(bi_lst) < 3:
            return
        if self.config.left_method == LeftSegMethod.PEAK:
            _high = max(bi._high() for bi in bi_lst)
            _low = min(bi._low() for bi in bi_lst)
            if abs(_high-bi_lst[0].get_begin_val()) >= abs(_low-bi_lst[0].get_begin_val()):
                peak_bi = find_peak_bi(bi_lst, is_high=True)
                assert peak_bi is not None
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BiDir.UP, split_first_seg=False, reason="0seg_find_high")
            else:
                peak_bi = find_peak_bi(bi_lst, is_high=False)
                assert peak_bi is not None
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BiDir.DOWN, split_first_seg=False, reason="0seg_find_low")
            self.collect_left_as_seg(bi_lst)
        elif self.config.left_method == LeftSegMethod.ALL:
            _dir = BiDir.UP if bi_lst[-1].get_end_val() >= bi_lst[0].get_begin_val() else BiDir.DOWN
            self.add_new_seg(bi_lst, bi_lst[-1].idx, is_sure=False, seg_dir=_dir, split_first_seg=False, reason="0seg_collect_all")
        else:
            raise ChanException(f"unknown seg left_method = {self.config.left_method}", ErrCode.PARA_ERROR)

    def collect_left_seg_peak_method(self, last_seg_end_bi, bi_lst):
        """
        使用峰值方法收集剩余的线段
        """
        if last_seg_end_bi.is_down():
            peak_bi = find_peak_bi(bi_lst[last_seg_end_bi.idx + 3:], is_high=True)
            if peak_bi and peak_bi.idx - last_seg_end_bi.idx >= 3:
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BiDir.UP, reason="collectleft_find_high")
        else:
            peak_bi = find_peak_bi(bi_lst[last_seg_end_bi.idx + 3:], is_high=False)
            if peak_bi and peak_bi.idx - last_seg_end_bi.idx >= 3:
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BiDir.DOWN, reason="collectleft_find_low")
        last_seg_end_bi = self[-1].end_bi

        self.collect_left_as_seg(bi_lst)

    def collect_segs(self, bi_lst):
        """
        收集线段
        """
        last_bi = bi_lst[-1]
        last_seg_end_bi = self[-1].end_bi
        if last_bi.idx-last_seg_end_bi.idx < 3:
            return
        if last_seg_end_bi.is_down() and last_bi.get_end_val() <= last_seg_end_bi.get_end_val():
            if peak_bi := find_peak_bi(bi_lst[last_seg_end_bi.idx + 3:], is_high=True):
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BiDir.UP, reason="collectleft_find_high_force")
                self.collect_left_seg(bi_lst)
        elif last_seg_end_bi.is_up() and last_bi.get_end_val() >= last_seg_end_bi.get_end_val():
            if peak_bi := find_peak_bi(bi_lst[last_seg_end_bi.idx + 3:], is_high=False):
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BiDir.DOWN, reason="collectleft_find_low_force")
                self.collect_left_seg(bi_lst)
        # 剩下线段的尾部相比于最后一个线段的尾部，高低关系和最后一个虚线段的方向一致
        elif self.config.left_method == LeftSegMethod.ALL:  # 容易找不到二类买卖点！！
            self.collect_left_as_seg(bi_lst)
        elif self.config.left_method == LeftSegMethod.PEAK:
            self.collect_left_seg_peak_method(last_seg_end_bi, bi_lst)
        else:
            raise ChanException(f"unknown seg left_method = {self.config.left_method}", ErrCode.PARA_ERROR)

    def collect_left_seg(self, bi_lst: BiList):
        """
        如果线段列表为空，则收集第一个线段，否则收集其他线段
        """
        if len(self) == 0:
            self.collect_first_seg(bi_lst)
        else:
            self.collect_segs(bi_lst)

    def collect_left_as_seg(self, bi_lst: BiList):
        """
        将剩余的笔收集为线段
        """
        last_bi = bi_lst[-1]
        last_seg_end_bi = self[-1].end_bi
        if last_seg_end_bi.idx+1 >= len(bi_lst):
            return
        if last_seg_end_bi.dir == last_bi.dir:
            self.add_new_seg(bi_lst, last_bi.idx-1, is_sure=False, reason="collect_left_1")
        else:
            self.add_new_seg(bi_lst, last_bi.idx, is_sure=False, reason="collect_left_0")

    def try_add_new_seg(self, bi_lst, end_bi_idx: int, is_sure=True, seg_dir=None, split_first_seg=True, reason="normal"):
        """
        尝试添加一个新的线段
        """
        if len(self) == 0 and split_first_seg and end_bi_idx >= 3:
            if peak_bi := find_peak_bi(bi_lst[end_bi_idx - 3::-1], bi_lst[end_bi_idx].is_down()):
                if (peak_bi.is_down() and (peak_bi._low() < bi_lst[0]._low() or peak_bi.idx == 0)) or \
                   (peak_bi.is_up() and (peak_bi._high() > bi_lst[0]._high() or peak_bi.idx == 0)):  # 要比第一笔开头还高/低（因为没有比较到）
                    self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=peak_bi.dir, reason="split_first_1st")
                    self.add_new_seg(bi_lst, end_bi_idx, is_sure=False, reason="split_first_2nd")
                    return
        bi1_idx = 0 if len(self) == 0 else self[-1].end_bi.idx+1
        bi1 = bi_lst[bi1_idx]
        bi2 = bi_lst[end_bi_idx]
        self.lst.append(Seg(len(self.lst), bi1, bi2, is_sure=is_sure, seg_dir=seg_dir, reason=reason))

        if len(self.lst) >= 2:
            self.lst[-2].next = self.lst[-1]
            self.lst[-1].pre = self.lst[-2]
        self.lst[-1].update_bi_list(bi_lst, bi1_idx, end_bi_idx)

    def add_new_seg(self, bi_lst: BiList, end_bi_idx: int, is_sure=True, seg_dir=None, split_first_seg=True, reason="normal"):
        """
        添加一个新的线段。如果添加失败，则返回False
        """
        try:
            self.try_add_new_seg(bi_lst, end_bi_idx, is_sure, seg_dir, split_first_seg, reason)
        except ChanException as e:
            if e.errcode == ErrCode.SEG_END_VALUE_ERR and len(self.lst) == 0:
                return False
            raise e
        except Exception as e:
            raise e
        return True

    @abc.abstractmethod
    def update(self, bi_lst: BiList):
        """
        抽象方法，子类需要实现它来更新线段列表
        """
        ...


def find_peak_bi(bi_lst: Union[BiList, List[Bi]], is_high):
    """
    在给定的笔列表中找到峰值笔。这可以是最高的上升笔或最低的下降笔
    """
    peak_val = float("-inf") if is_high else float("inf")
    peak_bi = None
    for bi in bi_lst:
        if (is_high and bi.get_end_val() >= peak_val and bi.is_up()) or (not is_high and bi.get_end_val() <= peak_val and bi.is_down()):
            if bi.pre and bi.pre.pre and ((is_high and bi.pre.pre.get_end_val() > bi.get_end_val()) or (not is_high and bi.pre.pre.get_end_val() < bi.get_end_val())):
                continue
            peak_val = bi.get_end_val()
            peak_bi = bi
    return peak_bi
