import abc
from typing import Iterable

class AbsStockApi:
    def __init__(self, code, k_type, begin_date, end_date, autype):
        self.code = code
        self.name = None
        self.is_stock = None
        self.k_type = k_type
        self.begin_date = begin_date
        self.end_date = end_date
        self.autype = autype
        self.set_base_info()

    @abc.abstractmethod
    def get_kl_data(self) -> Iterable:
        pass

    @classmethod
    def set_base_info(self):
        pass

    @classmethod
    def do_init(cls):
        pass

    @classmethod
    def do_close(cls):
        pass
