from typing import List, Optional, Union, overload

from data_process.common.cenum import FX_TYPE, KLINE_DIR
from data_process.kline.kline import CKLine

from .bi import CBi
from .bi_config import CBiConfig


class CBiList:
    def __init__(self, bi_conf=CBiConfig()):
        self.bi_list: List[CBi] = []
        self.last_end = None  # 最后一笔的尾部
        self.config = bi_conf

        self.free_klc_lst = []  # 仅仅用作第一笔未画出来之前的缓存，为了获得更精准的结果而已，不加这块逻辑其实对后续计算没太大影响

    def __str__(self):
        return "\n".join([str(bi) for bi in self.bi_list])

    def __iter__(self):
        yield from self.bi_list

    @overload
    def __getitem__(self, index: int) -> CBi: ...

    @overload
    def __getitem__(self, index: slice) -> List[CBi]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[CBi], CBi]:
        return self.bi_list[index]

    def __len__(self):
        return len(self.bi_list)

    def try_create_first_bi(self, klc: CKLine) -> bool:
        """
        尝试使用给定的K线`klc`创建第一笔
        如果成功创建了第一笔，返回`True`，否则将`klc`添加到`free_klc_lst`并返回`False`
        """
        # 遍历`free_klc_lst`中的每个K线，检查是否与`klc`有相反的分型，如果有，并且它们可以形成一笔，则添加这笔并设置`last_end`为`klc`
        for exist_free_klc in self.free_klc_lst:
            if exist_free_klc.fx == klc.fx:
                continue
            if self.can_make_bi(klc, exist_free_klc):
                self.add_new_bi(exist_free_klc, klc)
                self.last_end = klc
                return True
        self.free_klc_lst.append(klc)
        self.last_end = klc
        return False

    def update_bi(self, klc: CKLine, last_klc: CKLine, cal_virtual: bool) -> bool:
        """
        根据给定的K线`klc`和`last_klc`更新笔列表
        如果成功更新或添加了笔，返回`True`，否则返回`False`
        """
        # 首先更新确定的笔，然后根据`cal_virtual`决定是否尝试添加虚拟笔
        flag1 = self.update_bi_sure(klc)
        if cal_virtual:
            flag2 = self.try_add_virtual_bi(last_klc)
            return flag1 or flag2
        else:
            return flag1

    def update_bi_sure(self, klc: CKLine) -> bool:
        """
        根据给定的K线`klc`更新确定的笔
        """
        # 获取最后一笔的最后一个K线单元的索引
        _tmp_end = self.get_last_klu_of_last_bi()
        # 删除任何存在的虚拟笔
        self.delete_virtual_bi()
        # 如果传入的K线`klc`没有明确的分型（即顶或底），检查最后一笔的最后一个K线单元的索引是否已更改，并返回结果
        if klc.fx == FX_TYPE.UNKNOWN:
            return _tmp_end != self.get_last_klu_of_last_bi()
        # 如果不存在最后的结束K线或笔列表为空（即还没有创建任何笔），尝试创建第一笔
        if self.last_end is None or len(self.bi_list) == 0:
            return self.try_create_first_bi(klc)
        # 如果给定的K线`klc`的分型与最后的结束K线的分型相同，尝试更新最后一笔的结束
        if klc.fx == self.last_end.fx:
            return self.try_update_end(klc)
        # 如果`klc`和`last_end`可以形成一笔，添加一个新的笔，并更新`last_end`为`klc`
        elif self.can_make_bi(klc, self.last_end):
            self.add_new_bi(self.last_end, klc)
            self.last_end = klc
            return True

        # 如果上述所有条件都不满足，检查最后一笔的最后一个K线单元的索引是否已更改，并返回结果
        return _tmp_end != self.get_last_klu_of_last_bi()

    def delete_virtual_bi(self):
        """
        从笔列表中删除虚拟笔
        """
        # 如果笔列表的最后一笔是虚拟的
        if len(self) > 0 and not self.bi_list[-1].is_sure:
            # 如果这笔是虚拟结束，恢复它到确定的结束
            if self.bi_list[-1].is_virtual_end():
                self.bi_list[-1].restore_from_virtual_end()
            else:
                # 否则，从笔列表中删除这笔
                del self.bi_list[-1]

    def try_add_virtual_bi(self, klc: CKLine, need_del_end=False):
        """
        尝试添加一个虚拟笔
        返回`True`如果成功添加虚拟笔，否则返回`False`
        """
        # 如果`need_del_end`为`True`，则删除虚拟笔的结束
        if need_del_end:
            self.delete_virtual_bi()
        # 如果笔列表为空或`klc`与最后一笔的结束相同，返回`False`
        if len(self) == 0:
            return False
        if klc.idx == self[-1].end_klc.idx:
            return False

        # 根据`klc`的方向和最后一笔的方向，检查是否可以添加虚拟笔
        if (self[-1].is_up() and klc.high >= self[-1].end_klc.high) or (self[-1].is_down() and klc.low <= self[-1].end_klc.low):
            # 更新最后一笔为虚拟笔
            self.bi_list[-1].update_virtual_end(klc)
            return True

        _tmp_klc = klc
        # 主要目的是检查是否可以在给定的K线`klc`和最后一笔的结束之间形成一个新的虚拟笔
        # 首先确保`_tmp_klc`的索引大于最后一笔的结束索引，这是为了确保我们只考虑最后一笔结束之后的K线
        while _tmp_klc and _tmp_klc.idx > self[-1].end_klc.idx:
            assert _tmp_klc is not None
            if not self.satisfy_bi_span(_tmp_klc, self[-1].end_klc):
                return False

            # 接下来，根据最后一笔的方向和`_tmp_klc`的方向，检查是否可以形成一个新的虚拟笔：
            # - 如果最后一笔是下降的、`_tmp_klc`的方向是上升、并且`_tmp_klc`的低点大于最后一笔的结束低点，或者
            # - 如果最后一笔是上升的、`_tmp_klc`的方向是下降、并且`_tmp_klc`的高点小于最后一笔的结束高点，
            # - 并且最后一笔的结束和`_tmp_klc`之间的分型有效（通过`check_fx_valid`方法检查），
            # - 则可以形成一个新的虚拟笔
            if (
                    (self[-1].is_down() and _tmp_klc.dir == KLINE_DIR.UP and _tmp_klc.low > self[-1].end_klc.low) or
                    (self[-1].is_up() and _tmp_klc.dir == KLINE_DIR.DOWN and _tmp_klc.high < self[-1].end_klc.high)
            ) and self[-1].end_klc.check_fx_valid(_tmp_klc, self.config.bi_fx_check, for_virtual=True):
                # 新增一笔
                self.add_new_bi(self.last_end, _tmp_klc, is_sure=False)
                return True
            # 如果不满足上述条件，将`_tmp_klc`设置为其前一个K线，并继续循环
            _tmp_klc = _tmp_klc.pre
        # 如果循环结束时没有找到可以形成虚拟笔的K线，方法将返回`False`
        return False

    def add_new_bi(self, pre_klc, cur_klc, is_sure=True):
        """
        根据给定的K线`pre_klc`和`cur_klc`添加一个新的笔
        """
        self.bi_list.append(CBi(pre_klc, cur_klc, idx=len(self.bi_list), is_sure=is_sure))
        # 如果笔列表中至少有两笔，设置新笔的前一笔和前一笔的后一笔
        if len(self.bi_list) >= 2:
            self.bi_list[-2].next = self.bi_list[-1]
            self.bi_list[-1].pre = self.bi_list[-2]

    def satisfy_bi_span(self, klc: CKLine, last_end: CKLine):
        """
        检查给定的K线`klc`和`last_end`之间是否满足创建笔的跨度条件
        """
        # 如果配置为严格模式，跨度必须大于或等于4
        bi_span = self.get_klc_span(klc, last_end)
        if self.config.is_strict:
            return bi_span >= 4

        # 否则，跨度必须大于或等于3，并且K线单位数量也必须大于或等于3
        uint_kl_cnt = 0
        tmp_klc = last_end.next
        while tmp_klc:
            uint_kl_cnt += len(tmp_klc.lst)
            if not tmp_klc.next:  # 最后尾部虚笔的时候，可能klc.idx == last_end.idx+1
                return False
            if tmp_klc.next.idx < klc.idx:
                tmp_klc = tmp_klc.next
            else:
                break
        return bi_span >= 3 and uint_kl_cnt >= 3

    def get_klc_span(self, klc: CKLine, last_end: CKLine) -> int:
        """
        计算给定的K线`klc`和`last_end`之间的跨度
        如果配置中考虑缺口作为K线，遍历K线并检查它们之间是否有缺口，如果有，增加跨度
        """
        span = klc.idx - last_end.idx
        if not self.config.gap_as_kl:
            return span
        if span >= 4:  # 加速运算，如果span需要真正精确的值，需要去掉这一行
            return span
        tmp_klc = last_end
        while tmp_klc and tmp_klc.idx < klc.idx:
            if tmp_klc.has_gap_with_next():
                span += 1
            tmp_klc = tmp_klc.next
        return span

    def can_make_bi(self, klc: CKLine, last_end: CKLine):
        """
        检查是否可以根据给定的K线`klc`和`last_end`创建一个新的笔
        """
        if self.config.bi_algo == "fx":
            return True
        # 检查`klc`和`last_end`之间是否满足创建笔的跨度条件
        satisify_span = self.satisfy_bi_span(klc, last_end) if last_end.check_fx_valid(klc, self.config.bi_fx_check) else False
        # 如果满足条件并且配置要求笔的结束必须是峰值，检查是否满足峰值条件
        if satisify_span and self.config.bi_end_is_peak:
            return end_is_peak(last_end, klc)
        else:
            return satisify_span

    def try_update_end(self, klc: CKLine) -> bool:
        """
        检查给定的K线是否可以作为当前笔的新结束，并在满足条件的情况下进行更新
        """
        if len(self.bi_list) == 0:
            return False
        last_bi = self.bi_list[-1]
        # 如果最后一笔是上升的、`klc`是顶分型、并且`klc`的高点大于或等于最后一笔的结束高点，或者最后一笔是下降的、`klc`是底分型、并且`klc`的低点小于或等于最后一笔的结束低点，则更新最后一笔的结束
        if (last_bi.is_up() and klc.fx == FX_TYPE.TOP and klc.high >= last_bi.get_end_val()) or \
           (last_bi.is_down() and klc.fx == FX_TYPE.BOTTOM and klc.low <= last_bi.get_end_val()):
            last_bi.update_new_end(klc)
            self.last_end = klc
            return True
        else:
            return False

    def get_last_klu_of_last_bi(self) -> Optional[int]:
        """
        获取最后一笔的最后一个K线单位的索引
        """
        return self.bi_list[-1].get_end_klu().idx if len(self) > 0 else None


def end_is_peak(last_end: CKLine, cur_end: CKLine) -> bool:
    """
    检查当前结束的K线是否是一个峰值（对于上升趋势）或谷值（对于下降趋势）
    """
    if last_end.fx == FX_TYPE.BOTTOM:
        cmp_thred = cur_end.high  # 或者严格点选择get_klu_max_high()
        klc = last_end.get_next()
        while True:
            if klc.idx >= cur_end.idx:
                return True
            if klc.high > cmp_thred:
                return False
            klc = klc.get_next()
    elif last_end.fx == FX_TYPE.TOP:
        cmp_thred = cur_end.low  # 或者严格点选择get_klu_min_low()
        klc = last_end.get_next()
        while True:
            if klc.idx >= cur_end.idx:
                return True
            if klc.low < cmp_thred:
                return False
            klc = klc.get_next()
    return True
