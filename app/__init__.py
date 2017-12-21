from flask import Flask
from flask_login import LoginManager

from hub.HubConnection import HubConnection

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = 'secretkeyhereplease'

login_manager = LoginManager()
login_manager.init_app(app)

device_data_stack = list()
app.heart_rate_dict = dict()


def heart_rate_callback(args):
    if args['mac'] in app.heart_rate_dict:
        app.heart_rate_dict[args['mac']] = args['heart_rate']


app.hub = HubConnection(heart_rate_callback=heart_rate_callback, config=app.config)
app.hub_data_listener = app.hub.data_listener()
app.data = "{}"

from app import views
