from hub.HubConnection import HubConnection
import time

mac = 'CA:67:91:08:52:CE'

def callback(dict):
    print(dict)

myhub = HubConnection(callback)

myhub.request_token()