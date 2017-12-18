from hub.HubConnection import HubConnection
import time

mac = 'CA:67:91:08:52:CE'

def callback(dict):
    print(dict)

myhub = HubConnection(callback)
# dict = myhub.getConnectedDeviceList()
#
# for item in dict:
#     print(item)
#     print(dict[item])
#     print(dict[item].get('name'))

# myhub.stopMeasureHeartRate('CA:67:91:08:52:CE')
#
myhub.startMeasureHeartRate('CA:67:91:08:52:CE')
time.sleep(40)
myhub.stopMeasureHeartRate('CA:67:91:08:52:CE')
