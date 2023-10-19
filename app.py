from flask import Flask
from controllers.data_controller import data_blueprint


app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.register_blueprint(data_blueprint)

if __name__ == '__main__':
    app.run(debug=True, port=8008)
