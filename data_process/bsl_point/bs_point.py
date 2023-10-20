from typing import Dict, Generic, List, Optional, TypeVar, Union

from data_process.bi.bi import Bi
from data_process.chan_model.features import Features
from data_process.common.cenum import BspType
from data_process.seg.seg import Seg

LINE_TYPE = TypeVar('LINE_TYPE', Bi, Seg)


class BsPoint(Generic[LINE_TYPE]):
    def __init__(self, bi: LINE_TYPE, is_buy, bs_type: BspType, relate_bsp1: Optional['BsPoint'], feature_dict=None):
        self.bi: LINE_TYPE = bi
        self.klu = bi.get_end_klu()
        self.is_buy = is_buy
        self.type: List[BspType] = [bs_type]
        self.relate_bsp1 = relate_bsp1

        self.bi.bsp = self  # type: ignore
        self.features = Features(feature_dict)

        self.is_segbsp = False

    def add_type(self, bs_type: BspType):
        self.type.append(bs_type)

    def type2str(self):
        return ",".join([x.value for x in self.type])

    def add_another_bsp_prop(self, bs_type: BspType, relate_bsp1):
        self.add_type(bs_type)
        if self.relate_bsp1 is None:
            self.relate_bsp1 = relate_bsp1
        elif relate_bsp1 is not None:
            assert self.relate_bsp1.klu.idx == relate_bsp1.klu.idx

    def add_feat(self, inp1: Union[str, Dict[str, float], Dict[str, Optional[float]], 'Features'], inp2: Optional[float] = None):
        self.features.add_feat(inp1, inp2)
