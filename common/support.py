from data_process.common.cenum import BI_DIR


def get_json_data(chan_data):
    # merge_kline
    merge_kline_data = []
    for sublist in chan_data.lst:
        if len(sublist) > 1:
            merge_kline_data.append({
                'begin': {'value': sublist.low, 'timestamp': sublist[0].time.to_str()},
                'end': {'value': sublist.high, 'timestamp': sublist[-1].time.to_str()}
            })

    # data.lst
    kline_units_data = []
    kline_units = [item for sublst in chan_data.lst for item in sublst]
    for item in kline_units:
        item_data = {
            'open': item.open,
            'high': item.high,
            'low': item.low,
            'close': item.close,
            'timestamp': item.time.to_str(),
            'volume': item.trade_info.metric['volume']
        }

        kline_units_data.append(item_data)

    # data.bi_list
    bi_list_data = []
    for item in chan_data.bi_list:
        item_data = {}
        item_data['is_sure'] = item.is_sure
        if item.dir == BI_DIR.UP:
            item_data['begin'] = {
                'value': item.begin_klc.get_low_peak_klu().low,
                'timestamp': item.begin_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.end_klc.get_high_peak_klu().high,
                'timestamp': item.end_klc.get_low_peak_klu().time.to_str()
            }
        else:
            item_data['begin'] = {
                'value': item.end_klc.get_low_peak_klu().low,
                'timestamp': item.end_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.begin_klc.get_high_peak_klu().high,
                'timestamp': item.begin_klc.get_low_peak_klu().time.to_str()
            }

        bi_list_data.append(item_data)

    # data.seg_list
    seg_list_data = []
    for item in chan_data.seg_list:
        item_data = {}
        item_data['is_sure'] = item.is_sure
        if item.dir == BI_DIR.DOWN:
            item_data['begin'] = {
                'value': item.start_bi.begin_klc.get_high_peak_klu().high,
                'timestamp': item.start_bi.begin_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.end_bi.end_klc.get_low_peak_klu().low,
                'timestamp': item.end_bi.end_klc.get_low_peak_klu().time.to_str()
            }
        else:
            item_data['begin'] = {
                'value': item.start_bi.begin_klc.get_low_peak_klu().low,
                'timestamp': item.start_bi.begin_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.end_bi.end_klc.get_high_peak_klu().high,
                'timestamp': item.end_bi.end_klc.get_low_peak_klu().time.to_str()
            }

        seg_list_data.append(item_data)

    # data.zs_list
    zs_list_data = []
    for item in chan_data.zs_list:
        item_data = {}
        item_data['is_sure'] = item.is_sure
        if item.begin_bi.dir == BI_DIR.UP:
            item_data['begin'] = {
                'value': item.high,
                'timestamp': item.begin_bi.begin_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.low,
                'timestamp': item.end_bi.end_klc.get_low_peak_klu().time.to_str()
            }
        else:
            item_data['begin'] = {
                'value': item.low,
                'timestamp': item.end_bi.end_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.high,
                'timestamp': item.begin_bi.begin_klc.get_low_peak_klu().time.to_str()
            }

        zs_list_data.append(item_data)

    # segseg_list
    segseg_list_data = []
    for item in chan_data.segseg_list:
        item_data = {}
        item_data['is_sure'] = item.is_sure
        if item.dir == BI_DIR.DOWN:
            item_data['begin'] = {
                'value': item.start_bi.start_bi.begin_klc.get_high_peak_klu().high,
                'timestamp': item.start_bi.start_bi.begin_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.end_bi.end_bi.end_klc.get_low_peak_klu().low,
                'timestamp': item.end_bi.end_bi.end_klc.get_low_peak_klu().time.to_str()
            }
        else:
            item_data['begin'] = {
                'value': item.start_bi.start_bi.begin_klc.get_low_peak_klu().low,
                'timestamp': item.start_bi.start_bi.begin_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.end_bi.end_bi.end_klc.get_high_peak_klu().high,
                'timestamp': item.end_bi.end_bi.end_klc.get_low_peak_klu().time.to_str()
            }

        segseg_list_data.append(item_data)

    # segzs_list
    segzs_list_data = []
    for item in chan_data.segzs_list:
        item_data = {}
        item_data['is_sure'] = item.is_sure
        if item.begin_bi.dir == BI_DIR.UP:
            item_data['begin'] = {
                'value': item.high,
                'timestamp': item.begin_bi.start_bi.begin_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.low,
                'timestamp': item.end_bi.end_bi.end_klc.get_low_peak_klu().time.to_str()
            }
        else:
            item_data['begin'] = {
                'value': item.low,
                'timestamp': item.end_bi.end_bi.end_klc.get_low_peak_klu().time.to_str(),
            }
            item_data['end'] = {
                'value': item.high,
                'timestamp': item.begin_bi.start_bi.begin_klc.get_low_peak_klu().time.to_str()
            }

        segzs_list_data.append(item_data)

    return {
        'merge_kline_data': merge_kline_data,
        'kline_units_data': kline_units_data,
        'bi_list_data': bi_list_data,
        'seg_list_data': seg_list_data,
        'zs_list_data': zs_list_data,
        'segseg_list_data': segseg_list_data,
        'segzs_list_data': segzs_list_data,
    }