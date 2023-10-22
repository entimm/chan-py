import random
import numpy as np
from datetime import datetime, timedelta

from common.const import AuType, DataField, LvType
from common.func_util import parse_normal_date_str
from data_fetch.abs_stock_api import AbsStockApi


class GenerateFetcher(AbsStockApi):
    def __init__(self, code, k_type=LvType.K_DAY, begin_date=None, end_date=None, autype=AuType.QFQ):
        super(GenerateFetcher, self).__init__(code, k_type, begin_date, end_date, autype)


    def get_kl_data(self):
        def start_reach_limit(times=random.randint(1, 20)):
            def if_continue_reach_limit():
                nonlocal times
                times -= 1
                return times > 0

            return if_continue_reach_limit

        start_price = 100

        latest_price = start_price

        num_k_lines = 10000
        if_continue_reach_limit = start_reach_limit(0)
        for i in range(num_k_lines):
            # 随机决定这个时段内的最高波动和最低波动
            low_delta, high_delta = sorted(np.random.normal(0, 3, 2) / 100)
            # low_delta, high_delta = sorted((random.uniform(-10, 10) / 100,random.uniform(-10, 10) / 100))

            # 低于一块钱直接涨停
            if latest_price <= 1:
                if_continue_reach_limit = start_reach_limit()
            if if_continue_reach_limit():
                high_delta = low_delta = 0.1

            # 计算开盘、收盘、最高和最低价格
            high_price = latest_price * (1 + high_delta)
            low_price = latest_price * (1 + low_delta)
            open_price = random.uniform(low_price, high_price)
            close_price = random.uniform(low_price, high_price)

            # 更新当前价格
            latest_price = close_price

            # 保存K线数据
            date = (datetime(2000, 1, 1) + timedelta(i)).strftime('%Y-%m-%d')

            data_dict = {
                DataField.FIELD_TIME: parse_normal_date_str(date),
                DataField.FIELD_OPEN: open_price,
                DataField.FIELD_HIGH: high_price,
                DataField.FIELD_LOW: low_price,
                DataField.FIELD_CLOSE: close_price,
                DataField.FIELD_VOLUME: random.uniform(30, 100)
            }

            yield data_dict, False
