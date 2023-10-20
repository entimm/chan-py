from common.const import LvType
from common.time import Time


def str2float(s):
    try:
        return float(s)
    except ValueError:
        return 0.0


def kl_type_lt_day(_type):
    return _type in [LvType.K_1M, LvType.K_5M, LvType.K_15M, LvType.K_30M, LvType.K_60M]


def parse_normal_date_str(date_str):
    # 20210902113000000
    # 2021-09-13
    if len(date_str) == 10:
        year = int(date_str[:4])
        month = int(date_str[5:7])
        day = int(date_str[8:10])
        hour = minute = 0
    elif len(date_str) == 17:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(date_str[8:10])
        minute = int(date_str[10:12])
    elif len(date_str) == 19:
        year = int(date_str[:4])
        month = int(date_str[5:7])
        day = int(date_str[8:10])
        hour = int(date_str[11:13])
        minute = int(date_str[14:16])
    else:
        raise Exception(f"unknown time column:{date_str}")

    return Time(year, month, day, hour, minute)


def create_item_dict(data, column_name):
    for i in range(len(data)):
        data[i] = parse_normal_date_str(data[i]) if i == 0 else str2float(data[i])
    return dict(zip(column_name, data))
