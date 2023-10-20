from data_process.chan import Chan
from data_process.chan_config import ChanConfig
from data_process.common.cenum import BspType, FxType
from common.const import AuType, LvType
from data_fetch.manager import DataSrc

if __name__ == "__main__":
    """
    一个极其弱智的策略，只交易一类买卖点，底分型形成后就开仓，直到一类卖点顶分型形成后平仓
    只用做展示如何自己实现策略，做回测用~
    """
    code = "sz.000001"
    begin_time = "2021-01-01"
    end_time = None
    data_src = DataSrc.BAO_STOCK
    lv_list = [LvType.K_DAY]

    config = ChanConfig({
        "triger_step": True,  # 打开开关！
        "divergence_rate": 0.8,
        "min_zs_cnt": 1,
    })

    chan = Chan(
        code=code,
        begin_time=begin_time,
        end_time=end_time,
        data_src=data_src,
        lv_list=lv_list,
        config=config,
        autype=AuType.QFQ,
    )

    is_hold = False
    last_buy_price = None
    for chan_snapshot in chan.step_load():  # 每增加一根K线，返回当前静态精算结果
        bsp_list = chan_snapshot.get_bsp()  # 获取买卖点列表
        if not bsp_list:  # 为空
            continue
        last_bsp = bsp_list[-1]  # 最后一个买卖点
        if BspType.T1 not in last_bsp.type and BspType.T1P not in last_bsp.type:  # 加入只做1类买卖点
            continue

        cur_lv_chan = chan_snapshot[0]
        if cur_lv_chan[-2].fx == FxType.BOTTOM and last_bsp.is_buy and not is_hold:  # 底分型形成后开仓
            last_buy_price = cur_lv_chan[-1][-1].close  # 开仓价格为最后一根K线close
            print(f'{cur_lv_chan[-1][-1].time}:buy price = {last_buy_price}')
            is_hold = True
        elif cur_lv_chan[-2].fx == FxType.TOP and not last_bsp.is_buy and is_hold:  # 顶分型形成后平仓
            sell_price = cur_lv_chan[-1][-1].close
            print(f'{cur_lv_chan[-1][-1].time}:sell price = {sell_price}, profit rate = {(sell_price-last_buy_price)/last_buy_price*100:.2f}%')
            is_hold = False
