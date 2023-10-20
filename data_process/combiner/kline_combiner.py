from typing import Generic, Iterable, List, Optional, Self, TypeVar, Union, overload

from data_process.common.cache import MakeCache
from data_process.common.cenum import FxType, KlineDir
from data_process.common.chan_exception import ChanException, ErrCode
from data_process.kline.kline_unit import Kline_Unit
from .combine_item import CombineItem

T = TypeVar('T')


class KlineCombiner(Generic[T]):
    def __init__(self, kl_unit: T, _dir):
        item = CombineItem(kl_unit)
        self.__time_begin = item.time_begin
        self.__time_end = item.time_end
        self.__high = item.high
        self.__low = item.low

        self.__lst: List[T] = [kl_unit]  # 本级别每一根单位K线

        self.__dir = _dir
        self.__fx = FxType.UNKNOWN
        self.__pre: Optional[Self] = None
        self.__next: Optional[Self] = None

    def clean_cache(self):
        self._memoize_cache = {}

    @property
    def time_begin(self):
        return self.__time_begin

    @property
    def time_end(self):
        return self.__time_end

    @property
    def high(self):
        return self.__high

    @property
    def low(self):
        return self.__low

    @property
    def lst(self):
        return self.__lst

    @property
    def dir(self):
        return self.__dir

    @property
    def fx(self):
        return self.__fx

    @property
    def pre(self) -> Self:
        assert self.__pre is not None
        return self.__pre

    @property
    def next(self):
        return self.__next

    def get_next(self) -> Self:
        assert self.next is not None
        return self.next

    def test_combine(self, item: CombineItem, exclude_included=False, allow_hl_equal=None):
        """
        确定给定的item与当前K线合并器的关系，即它们是否可以合并，或者组合的趋势方向
        @param item
        @param exclude_included:如果为True，则在某些情况下不考虑被包含的K线
        @param allow_hl_equal:可以是None、1或-1，这个参数用于处理特定的被包含K线的情况，其中顶部或底部相等

        allow_hl_equal = None普通模式
        allow_hl_equal = 1 包含在了item中，顶部相等不合并
        allow_hl_equal = -1 包含在了item中，底部相等不合并
        """

        # K线合并器包含了item（包括等HL）
        if (self.high >= item.high and self.low <= item.low):
            return KlineDir.COMBINE
        # K线合并器被包含在了item中
        if (self.high <= item.high and self.low >= item.low):
            # 如果allow_hl_equal为1，且等H、item的L更低
            if allow_hl_equal == 1 and self.high == item.high and self.low > item.low:
                return KlineDir.DOWN
            # 如果allow_hl_equal为 - 1，且等L、item的H更高
            elif allow_hl_equal == -1 and self.low == item.low and self.high < item.high:
                return KlineDir.UP
            return KlineDir.INCLUDED if exclude_included else KlineDir.COMBINE
        # item的HL都更低
        if (self.high > item.high and self.low > item.low):
            return KlineDir.DOWN
        # item的HL都更高
        if (self.high < item.high and self.low < item.low):
            return KlineDir.UP
        else:
            raise ChanException("combine type unknown", ErrCode.COMBINER_ERR)

    def try_add(self, unit_kl: T, exclude_included=False, allow_hl_equal=None):
        """
        尝试将给定的unit_kl添加到当前K线合并器中，如果可以合并，则更新合并器的信息；否则，返回合并的方向
        """

        combine_item = CombineItem(unit_kl)
        _dir = self.test_combine(combine_item, exclude_included, allow_hl_equal)
        if _dir == KlineDir.COMBINE:
            self.__lst.append(unit_kl)
            if isinstance(unit_kl, Kline_Unit):
                unit_kl.set_klc(self)
            # 上升时，HL都取最高
            if self.dir == KlineDir.UP:
                if combine_item.high != combine_item.low or combine_item.high != self.high:  # 排除一字k线刚好在H上的，避免合并后也成一字
                    self.__high = max([self.high, combine_item.high])
                    self.__low = max([self.low, combine_item.low])
            # 下降时，HL都取最低
            elif self.dir == KlineDir.DOWN:
                if combine_item.high != combine_item.low or combine_item.low != self.low:  # 排除一字k线刚好在L上的，避免合并后也成一字
                    self.__high = min([self.high, combine_item.high])
                    self.__low = min([self.low, combine_item.low])
            else:
                raise ChanException(f"KLINE_DIR = {self.dir} err!!! must be {KlineDir.UP}/{KlineDir.DOWN}",
                                    ErrCode.COMBINER_ERR)
            self._time_end = combine_item.time_end
            self.clean_cache()
        # 返回UP/DOWN/COMBINE给KL_LIST，设置下一个的方向
        return _dir

    def get_peak_klu(self, is_high) -> T:
        # 获取最大值 or 最小值所在klu/bi
        return self.get_high_peak_klu() if is_high else self.get_low_peak_klu()

    @MakeCache
    def get_high_peak_klu(self) -> T:
        for kl in self.lst[::-1]:
            if CombineItem(kl).high == self.high:
                return kl
        raise ChanException("can't find peak...", ErrCode.COMBINER_ERR)

    @MakeCache
    def get_low_peak_klu(self) -> T:
        for kl in self.lst[::-1]:
            if CombineItem(kl).low == self.low:
                return kl
        raise ChanException("can't find peak...", ErrCode.COMBINER_ERR)

    def update_fx(self, _pre: Self, _next: Self, exclude_included=False, allow_hl_equal=None):
        """
        3根合并器的比较，更新K线合并器的分型信息
        """

        self.set_next(_next)
        self.set_pre(_pre)
        _next.set_pre(self)
        if exclude_included:
            # 当前H比前更高，比后也更高或等，L比后高
            if _pre.high < self.high and _next.high <= self.high and _next.low < self.low:
                # 如果allow_hl_equal=1，且当前H比后高
                if allow_hl_equal == 1 or _next.high < self.high:
                    self.__fx = FxType.TOP
            # 当前L比前更低，比后也更低或等，H比后低
            elif _pre.low > self.low and _next.low >= self.low and _next.high > self.high:
                # 如果allow_hl_equal=-1，且当前L比后低
                if allow_hl_equal == -1 or _next.low > self.low:
                    self.__fx = FxType.BOTTOM
        # 当前的HL比前后都更高(不含等)
        elif _pre.high < self.high and _next.high < self.high and _pre.low < self.low and _next.low < self.low:
            self.__fx = FxType.TOP
        # 当前的HL比前后都更低(不含等)
        elif _pre.high > self.high and _next.high > self.high and _pre.low > self.low and _next.low > self.low:
            self.__fx = FxType.BOTTOM
        self.clean_cache()

    def __str__(self):
        return f"{self.time_begin}~{self.time_end} {self.low}->{self.high}"

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> List[T]:
        ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[T], T]:
        return self.lst[index]

    def __len__(self):
        return len(self.lst)

    def __iter__(self) -> Iterable[T]:
        yield from self.lst

    def set_pre(self, _pre: Self):
        self.__pre = _pre
        self.clean_cache()

    def set_next(self, _next: Self):
        self.__next = _next
        self.clean_cache()
