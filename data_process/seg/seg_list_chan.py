from data_process.bi.bi_list import CBiList
from data_process.common.cenum import BI_DIR, SEG_TYPE

from .eigen_fx import CEigenFX
from .seg_config import CSegConfig
from .seg_list_comm import CSegListComm


class CSegListChan(CSegListComm):
    def __init__(self, seg_config=CSegConfig(), lv=SEG_TYPE.BI):
        super(CSegListChan, self).__init__(seg_config=seg_config, lv=lv)

    def do_init(self):
        # 删除线段列表末尾的不确定线段
        while len(self) and not self.lst[-1].is_sure:
            self.lst = self.lst[:-1]
        # 如果列表中存在确定的线段，并且该线段的特征分型的第三元素包含不确定的笔，则需要重新计算，因为线段分型元素的高低点可能不对
        if len(self):
            assert self.lst[-1].eigen_fx and self.lst[-1].eigen_fx.ele[-1]
            if not self.lst[-1].eigen_fx.ele[-1].lst[-1].is_sure:
                self.lst = self.lst[:-1]

    def update(self, bi_lst: CBiList):
        """
        更新线段列表
        """
        self.do_init()
        # 如果线段列表为空，则从头开始计算确定的线段，否则从最后一个线段的结束笔之后开始计算
        if len(self) == 0:
            self.cal_seg_sure(bi_lst, begin_idx=0)
        else:
            self.cal_seg_sure(bi_lst, begin_idx=self[-1].end_bi.idx+1)
        # 最后，收集剩余的线段
        self.collect_left_seg(bi_lst)

    def cal_seg_sure(self, bi_lst: CBiList, begin_idx: int):
        """
        计算确定的线段
        """
        up_eigen = CEigenFX(BI_DIR.UP, lv=self.lv)  # 上升线段下降笔
        down_eigen = CEigenFX(BI_DIR.DOWN, lv=self.lv)  # 下降线段上升笔
        last_seg_dir = None if len(self) == 0 else self[-1].dir
        # 遍历给定的笔列表，根据笔的方向和最后一个线段的方向，将笔添加到相应的特征分型中
        for bi in bi_lst[begin_idx:]:
            fx_eigen = None
            if bi.is_down() and last_seg_dir != BI_DIR.UP:
                if up_eigen.add(bi):
                    fx_eigen = up_eigen
            elif bi.is_up() and last_seg_dir != BI_DIR.DOWN:
                if down_eigen.add(bi):
                    fx_eigen = down_eigen
            if len(self) == 0:  # 尝试确定第一段方向，不要以谁先成为分形来决定，反例：US.EVRG
                if up_eigen.ele[1] is not None and bi.is_down():
                    last_seg_dir = BI_DIR.DOWN
                    down_eigen.clear()
                elif down_eigen.ele[1] is not None and bi.is_up():
                    up_eigen.clear()
                    last_seg_dir = BI_DIR.UP
                if up_eigen.ele[1] is None and last_seg_dir == BI_DIR.DOWN and bi.dir == BI_DIR.DOWN:
                    last_seg_dir = None
                elif down_eigen.ele[1] is None and last_seg_dir == BI_DIR.UP and bi.dir == BI_DIR.UP:
                    last_seg_dir = None

            # 如果特征分型完成，则调用`treat_fx_eigen`方法处理该特征分型
            if fx_eigen:
                self.treat_fx_eigen(fx_eigen, bi_lst)
                break

    def treat_fx_eigen(self, fx_eigen, bi_lst: CBiList):
        """
        处理给定的特征分型
        """
        _test = fx_eigen.can_be_end(bi_lst)
        end_bi_idx = fx_eigen.GetPeakBiIdx()
        # 首先检查特征分型是否可以结束
        if _test in [True, None]:  # None表示反向分型找到尾部也没找到
            is_true = _test is not None  # 如果是正常结束
            # 如果可以，则尝试添加一个新的线段
            # 如果线段添加成功，并且特征分型是正常结束的，则继续计算确定的线段
            if not self.add_new_seg(bi_lst, end_bi_idx, is_sure=is_true and fx_eigen.all_bi_is_sure()):  # 防止第一根线段的方向与首尾值异常
                self.cal_seg_sure(bi_lst, end_bi_idx+1)
                return
            self.lst[-1].eigen_fx = fx_eigen
            if is_true:
                self.cal_seg_sure(bi_lst, end_bi_idx + 1)
        # 如果特征分型不能结束，则从特征分型的第二个元素开始重新计算确定的线段
        else:
            self.cal_seg_sure(bi_lst, fx_eigen.lst[1].idx)
