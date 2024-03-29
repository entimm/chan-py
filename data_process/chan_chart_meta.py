from typing import List

from data_process.bi.bi import Bi
from data_process.bsl_point.bs_point import BsPoint
from data_process.common.cenum import FxType
from data_process.kline.kline import Kline
from data_process.kline.kline_list import Kline_List
from data_process.seg.eigen import Eigen
from data_process.seg.eigen_fx import EigenFX
from data_process.seg.seg import Seg
from data_process.zs.zs import Zs


class KlcMeta:
    def __init__(self, klc: Kline):
        self.high = klc.high
        self.low = klc.low
        self.begin_idx = klc.lst[0].idx
        self.end_idx = klc.lst[-1].idx
        self.type = klc.fx if klc.fx != FxType.UNKNOWN else klc.dir

        self.klu_list = list(klc.lst)


class BiMeta:
    def __init__(self, bi: Bi):
        self.idx = bi.idx
        self.dir = bi.dir
        self.type = bi.type
        self.begin_x = bi.get_begin_klu().idx
        self.end_x = bi.get_end_klu().idx
        self.begin_y = bi.get_begin_val()
        self.end_y = bi.get_end_val()
        self.is_sure = bi.is_sure


class SegMeta:
    def __init__(self, seg: Seg):
        if type(seg.begin_bi) == Bi:
            self.begin_x = seg.begin_bi.get_begin_klu().idx
            self.begin_y = seg.begin_bi.get_begin_val()
            self.end_x = seg.end_bi.get_end_klu().idx
            self.end_y = seg.end_bi.get_end_val()
        else:
            assert type(seg.begin_bi) == Seg
            self.begin_x = seg.begin_bi.begin_bi.get_begin_klu().idx
            self.begin_y = seg.begin_bi.begin_bi.get_begin_val()
            self.end_x = seg.end_bi.end_bi.get_end_klu().idx
            self.end_y = seg.end_bi.end_bi.get_end_val()
        self.dir = seg.dir
        self.is_sure = seg.is_sure

        self.tl = {}
        if seg.support_trend_line and seg.support_trend_line.line:
            self.tl["support"] = seg.support_trend_line
        if seg.resistance_trend_line and seg.resistance_trend_line.line:
            self.tl["resistance"] = seg.resistance_trend_line

    def format_tl(self, tl):
        assert tl.line
        tl_slope = tl.line.slope
        tl_x = tl.line.p.x
        tl_y = tl.line.p.y
        tl_y0 = self.begin_y
        tl_y1 = self.end_y
        tl_x0 = (tl_y0 - tl_y) / tl_slope + tl_x
        tl_x1 = (tl_y1 - tl_y) / tl_slope + tl_x
        return tl_x0, tl_y0, tl_x1, tl_y1


class EigenMeta:
    def __init__(self, eigen: Eigen):
        self.begin_x = eigen.lst[0].get_begin_klu().idx
        self.end_x = eigen.lst[-1].get_end_klu().idx
        self.begin_y = eigen.low
        self.end_y = eigen.high
        self.width = self.end_x - self.begin_x
        self.height = self.end_y - self.begin_y


class EigenFXMeta:
    def __init__(self, eigenFX: EigenFX):
        self.ele = [EigenMeta(ele) for ele in eigenFX.ele if ele is not None]
        assert len(self.ele) == 3
        assert eigenFX.ele[1] is not None
        self.gap = eigenFX.ele[1].gap
        self.fx = eigenFX.ele[1].fx

        self.begin_x = eigenFX.lst[0].get_begin_klu().idx
        self.begin_y = eigenFX.lst[0].get_begin_val()
        self.end_x = eigenFX.lst[-1].get_end_klu().idx
        self.end_y = eigenFX.lst[-1].get_end_val()


class ZsMeta:
    def __init__(self, zs: Zs):
        self.low = zs.low
        self.high = zs.high
        self.begin = zs.begin.idx
        self.end = zs.end.idx
        self.width = self.end - self.begin
        self.height = self.high - self.low
        self.is_sure = zs.is_sure
        self.sub_zs_lst = [ZsMeta(t) for t in zs.sub_zs_lst]
        self.is_onebi_zs = zs.is_one_bi_zs()


class BsPointMeta:
    def __init__(self, bsp: BsPoint, is_seg):
        self.is_buy = bsp.is_buy
        self.type = bsp.type2str()
        self.is_seg = is_seg

        self.x = bsp.klu.idx
        self.y = bsp.klu.low if self.is_buy else bsp.klu.high

    def desc(self):
        is_seg_flag = "※" if self.is_seg else ""
        return f'{is_seg_flag}b{self.type}' if self.is_buy else f'{is_seg_flag}s{self.type}'


class ChanChartMeta:
    def __init__(self, kl_list: Kline_List):
        self.data = kl_list

        self.klc_list: List[KlcMeta] = [KlcMeta(klc) for klc in kl_list.lst]
        self.datetick = [klu.time.to_str() for klu in self.klu_iter()]
        self.klu_len = sum(len(klc.klu_list) for klc in self.klc_list)

        self.bi_list = [BiMeta(bi) for bi in kl_list.bi_list]
        self.seg_list: List[SegMeta] = []
        self.eigenfx_lst: List[EigenFXMeta] = []
        for seg in kl_list.seg_list:
            self.seg_list.append(SegMeta(seg))
            if seg.eigen_fx:
                self.eigenfx_lst.append(EigenFXMeta(seg.eigen_fx))

        self.segseg_list: List[SegMeta] = [SegMeta(segseg) for segseg in kl_list.segseg_list]
        self.zs_lst: List[ZsMeta] = [ZsMeta(zs) for zs in kl_list.zs_list]
        self.segzs_lst: List[ZsMeta] = [ZsMeta(segzs) for segzs in kl_list.segzs_list]

        self.bs_point_lst: List[BsPointMeta] = [BsPointMeta(bs_point, is_seg=False) for bs_point in
                                                kl_list.bs_point_lst]
        self.seg_bsp_lst: List[BsPointMeta] = [BsPointMeta(seg_bsp, is_seg=True) for seg_bsp in
                                               kl_list.seg_bs_point_lst]

    def klu_iter(self):
        for klc in self.klc_list:
            yield from klc.klu_list

    def sub_last_kseg_start_idx(self, seg_cnt):
        if seg_cnt is None or len(self.data.seg_list) <= seg_cnt:
            return 0
        else:
            return self.data.seg_list[-seg_cnt].get_begin_klu().sub_kl_list[0].idx

    def sub_last_kbi_start_idx(self, bi_cnt):
        if bi_cnt is None or len(self.data.bi_list) <= bi_cnt:
            return 0
        else:
            return self.data.bi_list[-bi_cnt].begin_klc.lst[0].sub_kl_list[0].idx

    def sub_range_start_idx(self, x_range):
        for klc in self.data[::-1]:
            for klu in klc[::-1]:
                x_range -= 1
                if x_range == 0:
                    return klu.sub_kl_list[0].idx
        return 0
