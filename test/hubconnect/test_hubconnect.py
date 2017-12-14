from hub.HubConnection import HubConnection

myhub = HubConnection()
dict = myhub.getConnectedDeviceList()

for item in dict:
    print(item)
    print(dict[item])
    print(dict[item].get('name'))