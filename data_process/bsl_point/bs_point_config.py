from typing import Dict, List, Optional

from data_process.common.cenum import BspType, MacdAlgo
from data_process.common.func_util import _parse_inf

"""
- divergence_rate：1类买卖点背驰比例，即离开中枢的笔的 MACD 指标相对于进入中枢的笔，默认为 0.9
- min_zs_cnt：1类买卖点至少要经历几个中枢，默认为 1
- bsp1_only_multibi_zs: `min_zs_cnt` 计算的中枢至少 3 笔（少于 3 笔是因为开启了 `one_bi_zs` 参数），默认为 True；
- max_bs2_rate：2类买卖点那一笔回撤最大比例，默认为 0.618
    - 注：如果是 1.0，那么相当于允许回测到1类买卖点的位置
- bs1_peak：1类买卖点位置是否必须是整个中枢最低点，默认为 True
- macd_algo：MACD指标算法（可自定义）
    - peak：红绿柱最高点（绝对值），默认【线段买卖点不支持】
    - full_area：整根笔对应的MACD的面积【线段买卖点不支持】
    - area：整根笔对应的MACD的面积（只考虑相应红绿柱）【线段买卖点不支持】
    - slope：笔斜率
    - amp：笔的涨跌幅
    - diff：首尾K线对应的MACD柱子高度的差值的绝对值
    - amount：笔上所有K线成交额总和
    - volumn：笔上所有K线成交量总和
    - amount_avg：笔上K线平均成交额
    - volumn_avg：笔上K线平均成交量
    - turnrate_avg：笔上K线平均换手率
    - rsi: 笔上RSI值极值
- bs_type：关注的买卖点类型，逗号分隔，默认"1,1p,2,2s,3a,3b"
    - 1,2：分别表示1，2，3类买卖点
    - 2s：类二买卖点
    - 1p：盘整背驰1类买卖点
    - 3a：中枢出现在1类后面的3类买卖点（3-after）
    - 3b：中枢出现在1类前面的3类买卖点（3-before）
- "bsp2_follow_1"：2类买卖点是否必须跟在1类买卖点后面（用于小转大时1类买卖点因为背驰度不足没生成），默认为 True
- "bsp3_follow_1"：3类买卖点是否必须跟在1类买卖点后面（用于小转大时1类买卖点因为背驰度不足没生成），默认为 True
- "bsp3_peak"：3类买卖点突破笔是不是必须突破中枢里面最高/最低的，默认为 False
- "bsp2s_follow_2": 类2买卖点是否必须跟在2类买卖点后面（2类买卖点可能由于不满足 `max_bs2_rate` 最大回测比例条件没生成），默认为 False
- "max_bsp2s_lv": 类2买卖点最大层级（距离2类买卖点的笔的距离/2），默认为None，不做限制
- "strict_bsp3":3类买卖点对应的中枢必须紧挨着1类买卖点，默认为 False
"""


class BsPointConfig:
    def __init__(self, **args):
        self.b_conf = PointConfig(**args)
        self.s_conf = PointConfig(**args)

    def get_bs_config(self, is_buy):
        return self.b_conf if is_buy else self.s_conf


class PointConfig:
    def __init__(self,
                 divergence_rate,
                 min_zs_cnt,
                 bsp1_only_multibi_zs,
                 max_bs2_rate,
                 macd_algo,
                 bs1_peak,
                 bs_type,
                 bsp2_follow_1,
                 bsp3_follow_1,
                 bsp3_peak,
                 bsp2s_follow_2,
                 max_bsp2s_lv,
                 strict_bsp3,
                 ):
        self.divergence_rate = divergence_rate
        self.min_zs_cnt = min_zs_cnt
        self.bsp1_only_multibi_zs = bsp1_only_multibi_zs
        self.max_bs2_rate = max_bs2_rate
        assert self.max_bs2_rate <= 1
        self.set_macd_algo(macd_algo)
        self.bs1_peak = bs1_peak
        self.tmp_target_types = bs_type
        self.target_types: List[BspType] = []
        self.bsp2_follow_1 = bsp2_follow_1
        self.bsp3_follow_1 = bsp3_follow_1
        self.bsp3_peak = bsp3_peak
        self.bsp2s_follow_2 = bsp2s_follow_2
        self.max_bsp2s_lv: Optional[int] = max_bsp2s_lv
        self.strict_bsp3 = strict_bsp3

    def parse_target_type(self):
        _d: Dict[str, BspType] = {x.value: x for x in BspType}
        if isinstance(self.tmp_target_types, str):
            self.tmp_target_types = [t.strip() for t in self.tmp_target_types.split(",")]
        for target_t in self.tmp_target_types:
            assert target_t in ['1', '2', '3a', '2s', '1p', '3b']
        self.target_types = [_d[_type] for _type in self.tmp_target_types]

    def set_macd_algo(self, macd_algo):
        _d = {
            "area": MacdAlgo.AREA,
            "peak": MacdAlgo.PEAK,
            "full_area": MacdAlgo.FULL_AREA,
            "diff": MacdAlgo.DIFF,
            "slope": MacdAlgo.SLOPE,
            "amp": MacdAlgo.AMP,
            "amount": MacdAlgo.AMOUNT,
            "volumn": MacdAlgo.VOLUMN,
            "amount_avg": MacdAlgo.AMOUNT_AVG,
            "volumn_avg": MacdAlgo.VOLUMN_AVG,
            "turnrate_avg": MacdAlgo.AMOUNT_AVG,
            "rsi": MacdAlgo.RSI,
        }
        self.macd_algo = _d[macd_algo]

    def set(self, k, v):
        v = _parse_inf(v)
        if k == "macd_algo":
            self.set_macd_algo(v)
        else:
            exec(f"self.{k} = {v}")
