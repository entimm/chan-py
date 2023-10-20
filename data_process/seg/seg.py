from typing import Generic, List, Optional, Self, TypeVar

from data_process.bi.bi import Bi
from data_process.common.cenum import BiDir, MacdAlgo, TrendLineSide
from data_process.common.chan_exception import ChanException, ErrCode
from data_process.kline.kline_unit import Kline_Unit
from data_process.calculate.trend_line import TrendLine

from .eigen_fx import EigenFX

LINE_TYPE = TypeVar('LINE_TYPE', Bi, "CSeg")


class Seg(Generic[LINE_TYPE]):
    def __init__(self, idx: int, begin_bi: LINE_TYPE, end_bi: LINE_TYPE, is_sure=True, seg_dir=None, reason="normal"):
        """
        初始化一个线段，需要提供线段的索引、起始笔、结束笔、是否确定、线段方向和原因。
        """
        assert begin_bi.idx == 0 or begin_bi.dir == end_bi.dir or not is_sure, f"{begin_bi.idx} {end_bi.idx} {begin_bi.dir} {end_bi.dir}"
        self.idx = idx
        self.begin_bi = begin_bi
        self.end_bi = end_bi
        self.is_sure = is_sure
        self.dir = end_bi.dir if seg_dir is None else seg_dir

        from data_process.zs.zs import Zs
        self.zs_lst: List[Zs[LINE_TYPE]] = []

        self.eigen_fx: Optional[EigenFX] = None
        self.seg_idx = None  # 线段的线段用
        self.parent_seg: Optional[Seg] = None  # 在哪个线段里面
        self.pre: Optional[Self] = None
        self.next: Optional[Self] = None

        from data_process.bsl_point.bs_point import BsPoint
        self.bsp: Optional[BsPoint] = None  # 尾部是不是买卖点

        self.bi_list: List[LINE_TYPE] = []  # 仅通过self.update_bi_list来更新
        self.reason = reason
        self.support_trend_line = None
        self.resistance_trend_line = None
        if end_bi.idx - begin_bi.idx < 2:
            self.is_sure = False
        self.check()

    def set_seg_idx(self, idx):
        """
        设置线段索引
        """
        self.seg_idx = idx

    def check(self):
        """
        验证线段的有效性
        确保上升线段的起始值小于结束值，下降线段的起始值大于结束值
        确保线段的长度大于2
        """
        if not self.is_sure:
            return
        if self.is_down():
            if self.begin_bi.get_begin_val() < self.end_bi.get_end_val():
                raise ChanException(f"下降线段起始点应该高于结束点! idx={self.idx}", ErrCode.SEG_END_VALUE_ERR)
        elif self.begin_bi.get_begin_val() > self.end_bi.get_end_val():
            raise ChanException(f"上升线段起始点应该低于结束点! idx={self.idx}", ErrCode.SEG_END_VALUE_ERR)
        if self.end_bi.idx - self.begin_bi.idx < 2:
            raise ChanException(f"线段({self.begin_bi.idx}-{self.end_bi.idx})长度不能小于2! idx={self.idx}", ErrCode.SEG_LEN_ERR)

    def __str__(self):
        return f"{self.begin_bi.idx}->{self.end_bi.idx}: {self.dir}  {self.is_sure}"

    def add_zs(self, zs):
        """
        向线段添加中枢
        """
        self.zs_lst.append(zs)

    def cal_klu_slope(self):
        """
        计算线段的斜率，即结束值与开始值的差值除以它们之间的K线单元数量
        """
        assert self.end_bi.idx >= self.begin_bi.idx
        return (self.get_end_val()-self.get_begin_val())/(self.get_end_klu().idx-self.get_begin_klu().idx)/self.get_begin_val()

    def cal_amp(self):
        """
        计算线段的振幅，即结束值与开始值的差值
        """
        return (self.get_end_val()-self.get_begin_val())/self.get_begin_val()

    def cal_bi_cnt(self):
        """
        计算线段中的笔的数量
        """
        return self.end_bi.idx-self.begin_bi.idx+1

    def clear_zs_lst(self):
        """
        清空线段的中枢列表
        """
        self.zs_lst = []

    def _low(self):
        """
        获取线段的最低点
        """
        return self.end_bi.get_end_klu().low if self.is_down() else self.begin_bi.get_begin_klu().low

    def _high(self):
        """
        获取线段的最高点
        """
        return self.end_bi.get_end_klu().high if self.is_up() else self.begin_bi.get_begin_klu().high

    def is_down(self):
        """
        判断线段是否是下降的
        """
        return self.dir == BiDir.DOWN

    def is_up(self):
        """
        判断线段是否是上升的
        """
        return self.dir == BiDir.UP

    def get_end_val(self):
        """
        线段的结束
        """
        return self.end_bi.get_end_val()

    def get_begin_val(self):
        """
        线段的开始值
        @return:
        """
        return self.begin_bi.get_begin_val()

    def amp(self):
        """
        线段的振幅
        """
        return abs(self.get_end_val() - self.get_begin_val())

    def get_end_klu(self) -> Kline_Unit:
        """
        线段的结束的K线单元
        @return:
        """
        return self.end_bi.get_end_klu()

    def get_begin_klu(self) -> Kline_Unit:
        """
        线段的开始的K线单元
        @return:
        """
        return self.begin_bi.get_begin_klu()

    def get_klu_cnt(self):
        """
        线段中的K线单元数量
        """
        return self.get_end_klu().idx - self.get_begin_klu().idx + 1

    def cal_macd_metric(self, macd_algo, is_reverse):
        """
        根据给定的MACD算法（斜率或振幅）计算MACD指标
        """
        if macd_algo == MacdAlgo.SLOPE:
            return self.cal_macd_slope()
        elif macd_algo == MacdAlgo.AMP:
            return self.cal_macd_amp()
        else:
            raise ChanException(f"unsupport macd_algo={macd_algo} of Seg, should be one of slope/amp", ErrCode.PARA_ERROR)

    def cal_macd_slope(self):
        """
        计算线段的MACD斜率
        """
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_up():
            return (end_klu.high - begin_klu.low)/end_klu.high/(end_klu.idx - begin_klu.idx + 1)
        else:
            return (begin_klu.high - end_klu.low)/begin_klu.high/(end_klu.idx - begin_klu.idx + 1)

    def cal_macd_amp(self):
        """
        计算线段的MACD振幅
        """
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_down():
            return (begin_klu.high-end_klu.low)/begin_klu.high
        else:
            return (end_klu.high-begin_klu.low)/begin_klu.low

    def update_bi_list(self, bi_lst, idx1, idx2):
        """
        更新线段的笔列表，并设置支持和阻力趋势线
        """
        for bi_idx in range(idx1, idx2+1):
            bi_lst[bi_idx].parent_seg = self
            self.bi_list.append(bi_lst[bi_idx])
        if len(self.bi_list) >= 3:
            self.support_trend_line = TrendLine(self.bi_list, TrendLineSide.INSIDE)
            self.resistance_trend_line = TrendLine(self.bi_list, TrendLineSide.OUTSIDE)

    def get_first_multi_bi_zs(self):
        """
        线段中的第一个多笔中枢
        """
        return next((zs for zs in self.zs_lst if not zs.is_one_bi_zs()), None)

    def get_final_multi_bi_zs(self):
        """
        线段中的最后一个多笔中枢
        """
        return next((zs for zs in self.zs_lst[::-1] if not zs.is_one_bi_zs()), None)

    def get_multi_bi_zs_cnt(self):
        """
        线段中的多笔中枢数量
        """
        return sum(not zs.is_one_bi_zs() for zs in self.zs_lst)
