from common.const import AUTYPE
from data_fetch.manager import DATA_SRC
from data_process.chan import CChan
from data_process.chan_chart_meta import CChanChartMeta
from data_process.chan_config import CChanConfig


def make_chan_data(ticker, start, end, lv):
    chan = CChan(
        code=ticker,
        begin_time=start,
        end_time=end,
        data_src=DATA_SRC.LOCAL,
        lv_list=[lv],
        config=CChanConfig({
            "bi_strict": True,
            "divergence_rate": float("inf"),
            "bsp2_follow_1": False,
            "bsp3_follow_1": False,
            "min_zs_cnt": 0,
            "bs1_peak": False,
            "macd_algo": "peak",
            "bs_type": '1,2,3a,1p,2s,3b',
            "zs_algo": "normal",

            "triger_step": False,
            "skip_step": 0,
            "print_warning": True,
        }),
        autype=AUTYPE.QFQ,
    )

    return chan.kl_datas[lv]


def get_json_data(chan_data):
    meta = CChanChartMeta(chan_data)
    datetick = meta.datetick

    # data.lst
    kline_units_data = [{
        'timestamp': item.time.to_str(),
        'open': item.open,
        'high': item.high,
        'low': item.low,
        'close': item.close,
        'volume': item.trade_info.metric['volume']
    } for item in meta.klu_iter()]

    # merge_kline
    merge_kline_data = [{
        'begin': {'timestamp': datetick[item.begin_idx], 'value': item.low},
        'end': {'timestamp': datetick[item.end_idx], 'value': item.high}
    } for item in meta.klc_list]

    # data.bi_list
    bi_list_data = [{
        'is_sure': item.is_sure,
        'begin': {'timestamp':datetick[item.begin_x], 'value':item.begin_y},
        'end': {'timestamp':datetick[item.end_x], 'value':item.end_y},
    } for item in meta.bi_list]

    # data.seg_list
    seg_list_data = [{
        'is_sure': item.is_sure,
        'begin': {'timestamp':datetick[item.begin_x], 'value':item.begin_y},
        'end': {'timestamp':datetick[item.end_x], 'value':item.end_y},
    } for item in meta.seg_list]

    # segseg_list
    segseg_list_data = [{
        'is_sure': item.is_sure,
        'begin': {'timestamp':datetick[item.begin_x], 'value':item.begin_y},
        'end': {'timestamp':datetick[item.end_x], 'value':item.end_y},
    } for item in meta.segseg_list]

    # data.zs_list
    zs_list_data = [{
        'is_sure': item.is_sure,
        'begin': {'timestamp':datetick[item.begin], 'value':item.low},
        'end': {'timestamp':datetick[item.end], 'value':item.high},
    } for item in meta.zs_lst]

    # segzs_list
    segzs_list_data = [{
        'is_sure': item.is_sure,
        'begin': {'timestamp':datetick[item.begin], 'value':item.low},
        'end': {'timestamp':datetick[item.end], 'value':item.high},
    } for item in meta.segzs_lst]

    # eigenfx_lst
    eigenfx_lst_data = [{
        'begin': {'timestamp': datetick[item['begin_x']], 'value': item['begin_y']},
        'end': {'timestamp': datetick[item['end_x']], 'value': item['end_y']},
    } for item in (eigenMeta.__dict__ for item in meta.eigenfx_lst for eigenMeta in item.ele)]
    # eigenfxbi_lst
    eigenfxbi_lst_data = [{
        'begin': {'timestamp': datetick[item.begin_x], 'value': item.begin_y},
        'end': {'timestamp': datetick[item.end_x], 'value': item.end_y}
    } for item in meta.eigenfx_lst]
    # bs_point_lst
    # bs_point_lst_data = [item for item in meta.bs_point_lst_data]
    # seg_bsp_lst
    # seg_bsp_lst_data = [item for item in meta.seg_bsp_lst_data]

    return {
        'merge_kline_data': merge_kline_data,
        'kline_units_data': kline_units_data,
        'bi_list_data': bi_list_data,
        'seg_list_data': seg_list_data,
        'zs_list_data': zs_list_data,
        'segseg_list_data': segseg_list_data,
        'segzs_list_data': segzs_list_data,
        'eigenfx_lst_data': eigenfx_lst_data,
        'eigenfxbi_lst_data': eigenfxbi_lst_data,
        # 'bs_point_lst_data': bs_point_lst_data,
        # 'seg_bsp_lst_data': seg_bsp_lst_data,
    }
