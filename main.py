from flask import Flask, render_template

from common.const import AUTYPE, KL_TYPE
from common.support import get_json_data
from data_fetch.manager import DATA_SRC
from data_process.chan import CChan
from data_process.chan_config import CChanConfig


def make_chan_data(ticker, start, end, lv):
    data_src = DATA_SRC.GENERATE
    lv_list = [lv]

    chan = CChan(
        code=ticker,
        begin_time=start,
        end_time=end,
        data_src=data_src,
        lv_list=lv_list,
        config=CChanConfig({
            "bi_strict": True,
            "triger_step": False,
            "skip_step": 0,
            "divergence_rate": float("inf"),
            "bsp2_follow_1": False,
            "bsp3_follow_1": False,
            "min_zs_cnt": 0,
            "bs1_peak": False,
            "macd_algo": "peak",
            "bs_type": '1,2,3a,1p,2s,3b',
            "print_warning": True,
            "zs_algo": "normal",
        }),
        autype=AUTYPE.QFQ,
    )

    return chan.kl_datas[lv]


app = Flask(__name__, template_folder='web/templates', static_folder='web/static')


@app.route('/data')
def data():
    chan_data = make_chan_data('sh.000001', '2020-01-01', '2023-09-30', KL_TYPE.K_DAY)
    json_data = get_json_data(chan_data)

    return json_data


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=8008)
