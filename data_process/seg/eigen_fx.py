from typing import List, Optional

from data_process.bi.bi import CBi
from data_process.bi.bi_list import CBiList
from data_process.common.cenum import BI_DIR, FX_TYPE, KLINE_DIR, SEG_TYPE
from data_process.common.chan_exception import CChanException, ErrCode
from data_process.common.func_util import revert_bi_dir

from .eigen import CEigen


class CEigenFX:
    """
    特征序列分型
    """
    def __init__(self, _dir: BI_DIR, exclude_included=True, lv=SEG_TYPE.BI):
        self.lv = lv
        self.dir = _dir
        self.lst: List[CBi] = []

        # 特征序列分型的三个元素
        self.ele: List[Optional[CEigen]] = [None, None, None]
        # 布尔值，表示是否排除包含关系
        self.exclude_included = exclude_included
        # K线的方向
        self.kl_dir = KLINE_DIR.UP if _dir == BI_DIR.UP else KLINE_DIR.DOWN
        # 最后的证据笔
        self.last_evidence_bi: Optional[CBi] = None

    def treat_first_ele(self, bi: CBi) -> bool:
        """
        处理特征序列分型的第一个元素
        返回False，表示还没有形成分形
        """
        self.ele[0] = CEigen(bi, self.kl_dir)
        return False

    def treat_second_ele(self, bi: CBi) -> bool:
        """
        处理特征序列分型的第二个元素
        返回False，表示还没有形成分形
        """
        assert self.ele[0] is not None
        # 尝试将传入的笔`bi`与第一个元素合并
        combine_dir = self.ele[0].try_add(bi, exclude_included=self.exclude_included)
        # 如果不能合并
        if combine_dir != KLINE_DIR.COMBINE:
            # 创建一个新的特征序列对象，并将其设置为特征序列分型的第二个元素
            self.ele[1] = CEigen(bi, self.kl_dir)
            # 检查前两个特征序列元素是否可能形成分型，如果不可能，则重置特征序列分型
            if (self.is_up() and self.ele[1].high < self.ele[0].high) or \
               (self.is_down() and self.ele[1].low > self.ele[0].low):
                return self.reset()

        return False

    def treat_third_ele(self, bi: CBi) -> bool:
        """
        处理特征序列分型的第三个元素
        """
        assert self.ele[0] is not None
        assert self.ele[1] is not None
        self.last_evidence_bi = bi
        # 尝试将传入的笔`bi`与第二个元素合并
        allow_hl_equal = (1 if bi.is_down() else -1) if self.exclude_included else None
        combine_dir = self.ele[1].try_add(bi, allow_hl_equal=allow_hl_equal)
        # 如果可以合并，返回False
        if combine_dir == KLINE_DIR.COMBINE:
            return False
        # 创建一个新的特征序列对象，并将其设置为特征序列分型的第三个元素
        self.ele[2] = CEigen(bi, combine_dir)
        # 检查是否实际突破，如果没有实际突破，则重置特征序列
        if not self.actual_break():
            return self.reset()
        # 更新第二个特征序列元素为分型
        self.ele[1].update_fx(self.ele[0], self.ele[2], exclude_included=self.exclude_included, allow_hl_equal=allow_hl_equal)  # type: ignore

        # 根据分形的方向返回True或False
        fx = self.ele[1].fx
        is_fx = (self.is_up() and fx == FX_TYPE.TOP) or (self.is_down() and fx == FX_TYPE.BOTTOM)
        return True if is_fx else self.reset()

    def add(self, bi: CBi) -> bool:  # 返回是否出现分形
        """
        向特征序列分型中添加一个笔
        """
        assert bi.dir != self.dir
        self.lst.append(bi)
        # 逐个检查3个元素,找空的处理上
        if self.ele[0] is None:
            return self.treat_first_ele(bi)
        elif self.ele[1] is None:
            return self.treat_second_ele(bi)
        elif self.ele[2] is None:
            return self.treat_third_ele(bi)
        else:
            raise CChanException(f"特征序列3个都找齐了还没处理!! 当前笔:{bi.idx},当前:{str(self)}", ErrCode.SEG_EIGEN_ERR)

    def reset(self):
        """
        重置特征序列分型
        """
        # 如果`exclude_included`为True，清除特征序列并重新添加笔
        bi_tmp_list = list(self.lst[1:])
        if self.exclude_included:
            self.clear()
            for bi in bi_tmp_list:
                if self.add(bi):
                    return True
        # 否则，将第二和第三个元素设置为新的第一和第二个元素，并清除第三个元素
        else:
            assert self.ele[1] is not None
            ele2_begin_idx = self.ele[1].lst[0].idx
            self.ele[0], self.ele[1], self.ele[2] = self.ele[1], self.ele[2], None
            self.lst = [bi for bi in bi_tmp_list if bi.idx >= ele2_begin_idx]

        return False

    def can_be_end(self, bi_lst: CBiList):
        """
        判断特征序列分型是否可以结束
        """
        assert self.ele[1] is not None
        # 如果第二个特征序列元素有缺口，检查是否可以找到反转分型
        if self.ele[1].gap:
            assert self.ele[0] is not None
            end_bi_idx = self.GetPeakBiIdx()
            thred_value = bi_lst[end_bi_idx].get_end_val()
            break_thred = self.ele[0].low if self.is_up() else self.ele[0].high
            return self.find_revert_fx(bi_lst, end_bi_idx+2, thred_value, break_thred)
        else:
            return True

    def is_down(self):
        return self.dir == BI_DIR.DOWN

    def is_up(self):
        return self.dir == BI_DIR.UP

    def GetPeakBiIdx(self):
        """
        获取峰值笔的索引
        """
        assert self.ele[1] is not None
        # 返回第二个特征序列元素的峰值笔的索引
        return self.ele[1].GetPeakBiIdx()

    def all_bi_is_sure(self):
        """
        判断所有的笔是否确定
        """
        assert self.last_evidence_bi is not None
        # 遍历所有的笔，如果有一个笔不确定，则返回False
        return next((False for bi in self.lst if not bi.is_sure), self.last_evidence_bi.is_sure)

    def clear(self):
        self.ele = [None, None, None]
        self.lst = []

    def __str__(self):
        _t = [f"{[] if ele is None else ','.join([str(b.idx) for b in ele.lst])}" for ele in self.ele]
        return " | ".join(_t)

    def actual_break(self):
        """
        确定第三个特征序列元素是否实际突破了第二个特征序列元素
        """
        # 这意味着不需要检查实际突破，只要形成了分型就可以
        if not self.exclude_included:
            return True
        # 检查第三个特征序列元素的低点是否低于第二个特征序列元素的最后一个笔的低点，
        # 或者第三个特征序列元素的高点是否高于第二个特征序列元素的最后一个笔的高点。
        # 如果是，返回True
        assert self.ele[2] and self.ele[1]
        if (self.is_up() and self.ele[2].low < self.ele[1][-1]._low()) or \
           (self.is_down() and self.ele[2].high > self.ele[1][-1]._high()):  # 防止第二元素因为合并导致后面没有实际突破
            return True
        # 如果第三个特征序列元素的下一个笔和下下一个笔存在
        assert len(self.ele[2]) == 1
        ele2_bi = self.ele[2][0]
        if ele2_bi.next and ele2_bi.next.next:
            # 如果第三个特征序列元素是下降的，并且下下一个笔的低点低于第三个特征序列元素的低点，设置`last_evidence_bi`为下下一个笔并返回True
            if ele2_bi.is_down() and ele2_bi.next.next._low() < ele2_bi._low():
                self.last_evidence_bi = ele2_bi.next.next
                return True
            # 如果第三个特征序列元素是上升的，并且下下一个笔的高点高于第三个特征序列元素的高点，设置`last_evidence_bi`为下下一个笔并返回True
            elif ele2_bi.is_up() and ele2_bi.next.next._high() > ele2_bi._high():
                self.last_evidence_bi = ele2_bi.next.next
                return True
        # 如果上述条件都不满足，返回False
        return False

    def find_revert_fx(self, bi_list: CBiList, begin_idx: int, thred_value: float, break_thred: float):
        """
        寻找反转分型
        @param bi_list:笔的列表
        @param begin_idx:开始搜索的笔的索引
        @param thred_value:阈值，用于确定是否找到了反转分型
        @param break_thred:用于确定是否突破了前一个分型的第一个元素的极值
        """

        COMMON_COMBINE = True  # 是否用普通分形合并规则处理
        # 如果返回None，表示找到最后了
        # 获取第一个笔的方向
        first_bi_dir = bi_list[begin_idx].dir  # down则是要找顶分型
        # 创建一个新的特征序列分型对象，其方向与第一个笔的方向相反
        egien_fx = CEigenFX(revert_bi_dir(first_bi_dir), exclude_included=not COMMON_COMBINE, lv=self.lv)  # 顶分型的话要找上升线段
        for bi in bi_list[begin_idx::2]:
            # 尝试向特征序列分型中添加笔
            if egien_fx.add(bi):
                # 如果使用普通的分型合并规则，直接返回True
                if COMMON_COMBINE:
                    return True

                # 尝试确定特征序列分型是否可以结束。如果可以，返回True。如果不可以，重置特征序列分型并继续搜索
                while True:
                    _test = egien_fx.can_be_end(bi_list)
                    if _test in [True, None]:
                        self.last_evidence_bi = bi
                        return _test
                    elif not egien_fx.reset():
                        break
            # 如果当前笔的低点低于`thred_value`或高点高于`thred_value`，返回False
            if (bi.is_down() and bi._low() < thred_value) or (bi.is_up() and bi._high() > thred_value):
                return False
            # 如果已经有两个元素，并且突破了前一个分型的第一个元素的极值，返回True
            if egien_fx.ele[1] is not None and ((bi.is_down() and egien_fx.ele[1].high > break_thred) or (bi.is_up() and egien_fx.ele[1].low < break_thred)):
                return True

        # 如果遍历完了所有的笔而没有找到反转分型，返回None
        return None
