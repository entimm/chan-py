from data_process.combiner.kline_combiner import KlineCombiner
from data_process.common.cenum import FxCheckMethod, FxType, KlineDir
from data_process.common.chan_exception import ChanException, ErrCode
from data_process.common.func_util import has_overlap
from data_process.kline.kline_unit import Kline_Unit


# 合并后的K线
class Kline(KlineCombiner[Kline_Unit]):
    def __init__(self, kl_unit: Kline_Unit, idx, _dir=KlineDir.UP):
        super(Kline, self).__init__(kl_unit, _dir)
        self.idx: int = idx
        self.kl_type = kl_unit.kl_type
        kl_unit.set_klc(self)

    def __str__(self):
        fx_token = ""
        if self.fx == FxType.TOP:
            fx_token = "^"
        elif self.fx == FxType.BOTTOM:
            fx_token = "_"
        return f"{self.idx}th{fx_token}:{self.time_begin}~{self.time_end}({self.kl_type}|{len(self.lst)}) low={self.low} high={self.high}"

    def get_sub_klc(self):
        """
        获取子K线组合。
        注意：可能会出现相邻的两个KLC的子KLC会有重复，因为子KLU合并时正好跨过了父KLC的结束时间边界。
        """
        last_klc = None
        for klu in self.lst:
            for sub_klu in klu.get_children():
                if sub_klu.klc != last_klc:
                    last_klc = sub_klu.klc
                    yield sub_klu.klc

    def get_klu_max_high(self) -> float:
        """获取K线单元中的最高价"""
        return max(x.high for x in self.lst)

    def get_klu_min_low(self) -> float:
        """获取K线单元中的最低价"""
        return min(x.low for x in self.lst)

    def has_gap_with_next(self) -> bool:
        """检查当前K线与下一个K线之间是否有间隔"""
        assert self.next is not None
        # 相同也算重叠，也就是没有gap
        return not has_overlap(self.get_klu_min_low(), self.get_klu_max_high(), self.next.get_klu_min_low(), self.next.get_klu_max_high(), equal=True)

    def check_fx_valid(self, item2: "Kline", method, for_virtual=False):
        """
        检查是否满足有效的分型条件。
        for_virtual: 虚笔时使用。
        """
        # 确保当前K线与item2之间的关系是连续的，并且item2的索引大于当前K线的索引。
        assert self.next is not None and item2.pre is not None
        assert self.pre is not None
        assert item2.idx > self.idx
        # 检查顶分型
        if self.fx == FxType.TOP:
            # 如果不是虚笔，确保item2是底分型
            assert for_virtual or item2.fx == FxType.BOTTOM
            # 根据HALF方法，只检测前两个KLC来确定分型的有效性
            if method == FxCheckMethod.HALF:
                item2_high = max([item2.pre.high, item2.high])
                self_low = min([self.low, self.next.low])
            # 根据LOSS方法，只检测顶底分形KLC来确定分型的有效性
            elif method == FxCheckMethod.LOSS:
                item2_high = item2.high
                self_low = self.low
            # 根据STRICT或TOTALLY方法，检测更多的KLC来确定分型的有效性
            elif method in (FxCheckMethod.STRICT, FxCheckMethod.TOTALLY):
                # 如果是虚笔，只考虑item2的前一个KLC
                if for_virtual:
                    item2_high = max([item2.pre.high, item2.high])
                else:
                    # 确保item2有下一个K线
                    assert item2.next is not None
                    item2_high = max([item2.pre.high, item2.high, item2.next.high])
                self_low = min([self.pre.low, self.low, self.next.low])
            else:
                raise ChanException("bi_fx_check config error!", ErrCode.CONFIG_ERROR)
            # 根据TOTALLY方法返回结果
            if method == FxCheckMethod.TOTALLY:
                return self.low > item2_high
            else:
                return self.high > item2_high and item2.low < self_low
        # 检查底分型
        elif self.fx == FxType.BOTTOM:
            # 如果不是虚笔，确保item2是顶分型
            assert for_virtual or item2.fx == FxType.TOP
            # 根据HALF方法，只检测前两个KLC来确定分型的有效性
            if method == FxCheckMethod.HALF:
                item2_low = min([item2.pre.low, item2.low])
                cur_high = max([self.high, self.next.high])
            # 根据LOSS方法，只检测顶底分形KLC来确定分型的有效性
            elif method == FxCheckMethod.LOSS:
                item2_low = item2.low
                cur_high = self.high
            # 根据STRICT或TOTALLY方法，检测更多的KLC来确定分型的有效性
            elif method in (FxCheckMethod.STRICT, FxCheckMethod.TOTALLY):
                # 如果是虚笔，只考虑item2的前一个KLC
                if for_virtual:
                    item2_low = min([item2.pre.low, item2.low])
                else:
                    # 确保item2有下一个K线
                    assert item2.next is not None
                    item2_low = min([item2.pre.low, item2.low, item2.next.low])
                cur_high = max([self.pre.high, self.high, self.next.high])
            else:
                raise ChanException("bi_fx_check config error!", ErrCode.CONFIG_ERROR)
            # 根据TOTALLY方法返回结果
            if method == FxCheckMethod.TOTALLY:
                return self.high < item2_low
            else:
                return self.low < item2_low and item2.high > cur_high
        else:
            raise ChanException("only top/bottom fx can check_valid_top_button", ErrCode.BI_ERR)