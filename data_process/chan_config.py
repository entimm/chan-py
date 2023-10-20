from typing import List

from data_process.bi.bi_config import BiConfig
from data_process.bsl_point.bs_point_config import BsPointConfig
from data_process.common.cenum import TrendType
from data_process.common.chan_exception import ChanException, ErrCode
from data_process.common.func_util import _parse_inf
from data_process.calculate.boll import BollModel
from data_process.calculate.demark import DemarkEngine
from data_process.calculate.kdj import Kdj
from data_process.calculate.macd import Macd
from data_process.calculate.rsi import Rsi
from data_process.calculate.trend_model import TrendModel
from data_process.seg.seg_config import SegConfig
from data_process.zs.zs_config import ZsConfig

"""
- mean_metrics: 均线计算周期（用于生成特征及绘图时使用），默认为空[]
- trend_metrics: 计算上下轨道线周期，即 T 天内最高/低价格（用于生成特征及绘图时使用），默认为空[]
- boll_n: 布林线参数 N，整数，默认为 20（用于生成特征及绘图时使用）
- macd: MACD配置
    - fast: 默认为12
    - slow: 默认为26
    - signal: 默认为9
- cal_demark: 是否计算demark指标，默认为False
- demark: 德马克指标配置
    - demark_len: setup完成时长度，默认为9
    - setup_bias: setup比较偏移量，默认为4
    - countdown_bias: countdown比较偏移量，默认为2
    - max_countdown: 最大countdown数，默认为13
    - tiaokong_st: 序列真实起始位置计算时，如果setup第一根跳空，是否需要取前一根收盘价，默认为True
    - setup_cmp2close: setup计算当前K线的收盘价对比的是`setup_bias`根K线前的close，如果不是，下跌setup对比的是low，上升对比的是close，默认为True
    - countdown_cmp2close: countdown计算当前K线的收盘价对比的是`countdown_bias`根K线前的close，如果不是，下跌setup对比的是low，上升对比的是close，默认为True
- cal_rsi: 是否计算rsi指标，默认为False
- rsi:
    - rsi_cycle: rsi计算周期，默认为14
- cal_kdj: 是否计算kdj指标，默认为False
- kdj:
    - kdj_cycle: kdj计算周期，默认为9
- triger_step: 是否回放逐步返回，默认为 False
    - 用于逐步回放绘图时使用，此时 CChan 会变成一个生成器，每读取一根新K线就会计算一次当前所有指标，返回当前帧指标状况；常用于返回给 CAnimateDriver 绘图
- skip_step: triger_step 为 True 时有效，指定跳过前面几根K线，默认为 0；
- kl_data_check: 是否需要检验K线数据，检查项包括时间线是否有乱序，大小级别K线是否有缺失；默认为 True
- max_kl_misalgin_cnt: 在次级别找不到K线最大条数，默认为 2（次级别数据有缺失），`kl_data_check` 为 True 时生效
- max_kl_inconsistent_cnt: 天K线以下（包括）子级别和父级别日期不一致最大允许条数（往往是父级别数据有缺失），默认为 5，`kl_data_check` 为 True 时生效
- print_warning: 打印K线不一致的明细，默认为 True
- print_err_time: 计算发生错误时打印因为什么时间的K线数据导致的，默认为 False
- auto_skip_illegal_sub_lv: 如果获取次级别数据失败，自动删除该级别（比如指数数据一般不提供分钟线），默认为 False
"""

class ChanConfig:
    def __init__(self, conf=None):
        if conf is None:
            conf = {}
        conf = ConfigWithCheck(conf)
        self.bi_conf = BiConfig(
            bi_algo=conf.get("bi_algo", "normal"),
            is_strict=conf.get("bi_strict", True),
            bi_fx_check=conf.get("bi_fx_check", "strict"),
            gap_as_kl=conf.get("gap_as_kl", False),
            bi_end_is_peak=conf.get('bi_end_is_peak', True),

        )
        self.seg_conf = SegConfig(
            seg_algo=conf.get("seg_algo", "chan"),
            left_method=conf.get("left_seg_method", "peak"),
        )
        self.zs_conf = ZsConfig(
            need_combine=conf.get("zs_combine", True),
            zs_combine_mode=conf.get("zs_combine_mode", "zs"),
            one_bi_zs=conf.get("one_bi_zs", False),
            zs_algo=conf.get("zs_algo", "normal"),
        )

        self.triger_step = conf.get("triger_step", False)
        self.skip_step = conf.get("skip_step", 0)

        self.kl_data_check = conf.get("kl_data_check", True)
        self.max_kl_misalgin_cnt = conf.get("max_kl_misalgin_cnt", 2)
        self.max_kl_inconsistent_cnt = conf.get("max_kl_inconsistent_cnt", 5)
        self.auto_skip_illegal_sub_lv = conf.get("auto_skip_illegal_sub_lv", False)
        self.print_warning = conf.get("print_warning", True)
        self.print_err_time = conf.get("print_err_time", False)

        self.mean_metrics: List[int] = conf.get("mean_metrics", [])
        self.trend_metrics: List[int] = conf.get("trend_metrics", [])
        self.macd_config = conf.get("macd", {"fast": 12, "slow": 26, "signal": 9})
        self.cal_demark = conf.get("cal_demark", False)
        self.cal_rsi = conf.get("cal_rsi", False)
        self.cal_kdj = conf.get("cal_kdj", False)
        self.rsi_cycle = conf.get("rsi_cycle", 14)
        self.kdj_cycle = conf.get("kdj_cycle", 9)
        self.demark_config = conf.get("demark", {
            'demark_len': 9,
            'setup_bias': 4,
            'countdown_bias': 2,
            'max_countdown': 13,
            'tiaokong_st': True,
            'setup_cmp2close': True,
            'countdown_cmp2close': True,
        })
        self.boll_n = conf.get("boll_n", 20)

        self.set_bsp_config(conf)

        conf.check()

    def get_metric_model(self):
        res: List[Macd | TrendModel | BollModel | DemarkEngine | Rsi | Kdj] = [
            Macd(
                fastperiod=self.macd_config['fast'],
                slowperiod=self.macd_config['slow'],
                signalperiod=self.macd_config['signal'],
            )
        ]
        res.extend(TrendModel(TrendType.MEAN, mean_T) for mean_T in self.mean_metrics)

        for trend_T in self.trend_metrics:
            res.append(TrendModel(TrendType.MAX, trend_T))
            res.append(TrendModel(TrendType.MIN, trend_T))
        res.append(BollModel(self.boll_n))
        if self.cal_demark:
            res.append(DemarkEngine(
                demark_len=self.demark_config['demark_len'],
                setup_bias=self.demark_config['setup_bias'],
                countdown_bias=self.demark_config['countdown_bias'],
                max_countdown=self.demark_config['max_countdown'],
                tiaokong_st=self.demark_config['tiaokong_st'],
                setup_cmp2close=self.demark_config['setup_cmp2close'],
                countdown_cmp2close=self.demark_config['countdown_cmp2close'],
            ))
        if self.cal_rsi:
            res.append(Rsi(self.rsi_cycle))
        if self.cal_kdj:
            res.append(Kdj(self.kdj_cycle))
        return res

    def set_bsp_config(self, conf):
        para_dict = {
            "divergence_rate": float("inf"),
            "min_zs_cnt": 1,
            "bsp1_only_multibi_zs": True,
            "max_bs2_rate": 0.9999,
            "macd_algo": "peak",
            "bs1_peak": True,
            "bs_type": "1,1p,2,2s,3a,3b",
            "bsp2_follow_1": True,
            "bsp3_follow_1": True,
            "bsp3_peak": False,
            "bsp2s_follow_2": False,
            "max_bsp2s_lv": None,
            "strict_bsp3": False,
            }
        args = {para: conf.get(para, default_value) for para, default_value in para_dict.items()}
        self.bs_point_conf = BsPointConfig(**args)

        self.seg_bs_point_conf = BsPointConfig(**args)
        self.seg_bs_point_conf.b_conf.set("macd_algo", "slope")
        self.seg_bs_point_conf.s_conf.set("macd_algo", "slope")
        self.seg_bs_point_conf.b_conf.set("bsp1_only_multibi_zs", False)
        self.seg_bs_point_conf.s_conf.set("bsp1_only_multibi_zs", False)

        for k, v in conf.items():
            if isinstance(v, str):
                v = f'"{v}"'
            v = _parse_inf(v)
            if k.endswith("-buy"):
                prop = k.replace("-buy", "")
                exec(f"self.bs_point_conf.b_conf.set('{prop}', {v})")
            elif k.endswith("-sell"):
                prop = k.replace("-sell", "")
                exec(f"self.bs_point_conf.s_conf.set('{prop}', {v})")
            elif k.endswith("-segbuy"):
                prop = k.replace("-segbuy", "")
                exec(f"self.seg_bs_point_conf.b_conf.set('{prop}', {v})")
            elif k.endswith("-segsell"):
                prop = k.replace("-segsell", "")
                exec(f"self.seg_bs_point_conf.s_conf.set('{prop}', {v})")
            elif k.endswith("-seg"):
                prop = k.replace("-seg", "")
                exec(f"self.seg_bs_point_conf.b_conf.set('{prop}', {v})")
                exec(f"self.seg_bs_point_conf.s_conf.set('{prop}', {v})")
            elif k in args:
                exec(f"self.bs_point_conf.b_conf.set({k}, {v})")
                exec(f"self.bs_point_conf.s_conf.set({k}, {v})")
            else:
                raise ChanException(f"unknown para = {k}", ErrCode.PARA_ERROR)
        self.bs_point_conf.b_conf.parse_target_type()
        self.bs_point_conf.s_conf.parse_target_type()
        self.seg_bs_point_conf.b_conf.parse_target_type()
        self.seg_bs_point_conf.s_conf.parse_target_type()


class ConfigWithCheck:
    def __init__(self, conf):
        self.conf = conf

    def get(self, k, default_value=None):
        res = self.conf.get(k, default_value)
        if k in self.conf:
            del self.conf[k]
        return res

    def items(self):
        visit_keys = set()
        for k, v in self.conf.items():
            yield k, v
            visit_keys.add(k)
        for k in visit_keys:
            del self.conf[k]

    def check(self):
        if len(self.conf) > 0:
            invalid_key_lst = ",".join(list(self.conf.keys()))
            raise ChanException(f"invalid CChanConfig: {invalid_key_lst}", ErrCode.PARA_ERROR)
