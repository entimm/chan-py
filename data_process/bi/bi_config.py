from data_process.common.cenum import FX_CHECK_METHOD
from data_process.common.chan_exception import CChanException, ErrCode

"""
- bi_algo: 笔算法，默认为 normal
  - normal: 按缠论笔定义来算
  - fx: 顶底分形即成笔
- bi_strict：是否只用严格笔(bi_algo=normal时有效)，默认为 Ture[中枢算法](#中枢算法)
- gap_as_kl：缺口是否处理成一根K线，默认为 True
- bi_end_is_peak: 笔的尾部是否是整笔中最低/最高, 默认为 True
- bi_fx_check：检查笔顶底分形是否成立的方法
    - strict(默认)：底分型的最低点必须比顶分型3元素最低点的最小值还低，顶分型反之
    - totally: 底分型3元素的最高点必须必顶分型三元素的最低点还低
    - loss：底分型的最低点比顶分型中间元素低点还低，顶分型反之
    - half:对于上升笔，底分型的最低点比顶分型前两元素最低点还低，顶分型的最高点比底分型后两元素高点还高，下降笔反之
"""


class CBiConfig:
    def __init__(
            self,
            bi_algo="normal",
            is_strict=True,
            bi_fx_check="half",
            gap_as_kl=True,
            bi_end_is_peak=True,
    ):
        self.bi_algo = bi_algo
        self.is_strict = is_strict

        bi_fx_check_values = {
            "strict": FX_CHECK_METHOD.STRICT,
            "loss": FX_CHECK_METHOD.LOSS,
            "half": FX_CHECK_METHOD.HALF,
            "totally": FX_CHECK_METHOD.TOTALLY
        }
        if bi_fx_check in bi_fx_check_values:
            self.bi_fx_check = bi_fx_check_values[bi_fx_check]
        else:
            raise CChanException(f"unknown bi_fx_check={bi_fx_check}", ErrCode.PARA_ERROR)

        self.gap_as_kl = gap_as_kl
        self.bi_end_is_peak = bi_end_is_peak
