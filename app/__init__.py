from flask import Flask
from flask_login import LoginManager

from hub.HubConnection import HubConnection

app = Flask(__name__)
app.secret_key = 'secretkeyhereplease'

login_manager = LoginManager()
login_manager.init_app(app)

device_data_stack = list()

app.hub = HubConnection()
app.hub_data_listener = app.hub.data_listener()
app.data = "{}"

from app import views
