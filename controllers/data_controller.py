from flask import Blueprint, render_template

from biz.chart import make_chan_data, get_json_data
from common.const import KL_TYPE


data_blueprint = Blueprint('data', __name__)

@data_blueprint.route('/')
def get_index():
    return render_template('index.html')

@data_blueprint.route('/data')
def get_data():
    chan_data = make_chan_data('sh.000001', '2020-01-01', '2023-09-30', KL_TYPE.K_DAY)
    json_data = get_json_data(chan_data)
    return json_data

