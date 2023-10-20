"""
- 中枢
  - zs_combine：是否进行中枢合并，默认为 True
  - zs_combine_mode： 中枢合并模式，取值
      - zs：两中枢区间有重叠才合并（默认）
      - peak：两中枢有K线重叠就合并
  - one_bi_zs：是否需要计算只有一笔的中枢（分析趋势时会用到），默认为 False
  - zs_algo: 中枢算法normal/over_seg（段内中枢和跨段中枢，具体参见[中枢算法](#中枢算法)章节），默认为normal
"""

class ZsConfig:
    def __init__(self, need_combine=True, zs_combine_mode="zs", one_bi_zs=False, zs_algo="normal"):
        self.need_combine = need_combine
        self.zs_combine_mode = zs_combine_mode
        self.one_bi_zs = one_bi_zs
        self.zs_algo = zs_algo
