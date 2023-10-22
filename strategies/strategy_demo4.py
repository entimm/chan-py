from common.const import LvType, AuType
from data_fetch.fetchers.baostock_fetcher import BaostockFetcher
from data_fetch.manager import DataSrc
from data_process.chan import Chan
from data_process.chan_config import ChanConfig

if __name__ == "__main__":
    """
    本demo演示当你要用多级别trigger load的时候，如何巧妙的解决时间对齐的问题：
    解决方案就是喂第一根最大级别的时候，直接把所有的次级别全部喂进去
    之后每次只需要喂一根最大级别即可，复用框架内置的K线时间对齐能力
    从而避免了在trigger_load入参那里进行K线对齐，自己去找出最大级别那根K线下所有次级别的K线
    """
    code = "sz.000001"
    begin_time = "2023-06-01"
    end_time = None
    data_src = DataSrc.BAOSTOCK
    lv_list = [LvType.K_DAY, LvType.K_30M]

    config = ChanConfig({
        "triger_step": True,
        "divergence_rate": 0.8,
        "min_zs_cnt": 1,
    })

    chan = Chan(
        code=code,
        begin_time=begin_time,  # 已经没啥用了这一行
        end_time=end_time,  # 已经没啥用了这一行
        data_src=data_src,  # 已经没啥用了这一行
        lv_list=lv_list,
        config=config,
        autype=AuType.QFQ,  # 已经没啥用了这一行
    )
    BaostockFetcher.do_init()
    data_src_day = BaostockFetcher(code, k_type=LvType.K_DAY, begin_date=begin_time, end_date=end_time, autype=AuType.QFQ)
    data_src_30m = BaostockFetcher(code, k_type=LvType.K_30M, begin_date=begin_time, end_date=end_time, autype=AuType.QFQ)
    kl_30m_all = list(data_src_30m.get_kl_data())

    for _idx, klu in enumerate(data_src_day.get_kl_data()):
        # 本质是每喂一根日线的时候，这根日线之前的都要喂过，提前喂多点不要紧，框架会自动根据日线来截取需要的30M K线
        # 30M一口气全部喂完，后续就不用关注时间对齐的问题了
        if _idx == 0:
            chan.trigger_load({LvType.K_DAY: [klu], LvType.K_30M: kl_30m_all})
        else:
            chan.trigger_load({LvType.K_DAY: [klu]})

        if _idx == 4:  # demo只检查4根日线
            break
        # 检查时间对齐
        print("当前所有日线:", [klu.time.to_str() for klu in chan[0].klu_iter()])
        print("当前所有30M K线:", [klu.time.to_str() for klu in chan[1].klu_iter()], "\n")

    BaostockFetcher.do_close()