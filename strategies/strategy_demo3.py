import copy
from typing import List

from data_process.chan import Chan
from data_process.chan_config import ChanConfig
from common.const import AuType, DataField, LvType
from data_fetch.manager import DataSrc
from data_fetch.fetchers.baostock_fetcher import BaostockFetcher
from data_process.kline.kline_unit import Kline_Unit


def combine_60m_klu_form_15m(klu_15m_lst: List[Kline_Unit]) -> Kline_Unit:
    return Kline_Unit(
        {
            DataField.FIELD_TIME: klu_15m_lst[-1].time,
            DataField.FIELD_OPEN: klu_15m_lst[0].open,
            DataField.FIELD_CLOSE: klu_15m_lst[-1].close,
            DataField.FIELD_HIGH: max(klu.high for klu in klu_15m_lst),
            DataField.FIELD_LOW: min(klu.low for klu in klu_15m_lst),
        }
    )


if __name__ == "__main__":
    """
    代码不能直接跑，仅用于展示如何实现小级别K线更新直接刷新CChan结果
    """
    code = "sz.000001"
    begin_time = "2023-09-10"
    end_time = None
    data_src_type = DataSrc.BAOSTOCK
    lv_list = [LvType.K_60M, LvType.K_15M]

    config = ChanConfig({
        "triger_step": True,
    })

    # 快照
    chan_snapshot = Chan(
        code=code,
        data_src=data_src_type,
        lv_list=lv_list,
        config=config,
    )
    BaostockFetcher.do_init()
    data_src = BaostockFetcher(code, k_type=LvType.K_15M, begin_date=begin_time, end_date=end_time, autype=AuType.QFQ)  # 获取最小级别

    klu_15m_lst_tmp: List[Kline_Unit] = []  # 存储用于合成当前60M K线的15M k线

    for klu_15m in data_src.get_kl_data():  # 获取单根15分钟K线
        klu_15m = Kline_Unit(*klu_15m)
        klu_15m_lst_tmp.append(klu_15m)
        klu_60m = combine_60m_klu_form_15m(klu_15m_lst_tmp)  # 合成60分钟K线

        """
        拷贝一份chan_snapshot
        如果是用序列化方式，这里可以采用pickle.load()
        """
        chan: Chan = copy.deepcopy(chan_snapshot)
        chan.trigger_load({LvType.K_60M: [klu_60m], LvType.K_15M: klu_15m_lst_tmp})

        """
        策略开始：
        这里基于chan实现你的策略
        """
        for kl_type, ele_manager in chan.kl_datas.items():
            # 打印当前每一级别分别有多少K线
            print(klu_15m.time, kl_type, sum(len(klc) for klc in ele_manager))
        # 策略结束：

        if len(klu_15m_lst_tmp) == 4:  # 已经完成4根15分钟K线了，说明这个最新的60分钟K线和里面的4根15分钟K线在将来不会再变化
            """
            把当前完整chan重新保存成chan_snapshot
            如果是序列化方式，这里可以采用pickle.dump()
            """
            chan_snapshot = chan
            klu_15m_lst_tmp = []  # 清空1分钟K线，用于下一个五分钟周期的合成

    BaostockFetcher.do_close()
