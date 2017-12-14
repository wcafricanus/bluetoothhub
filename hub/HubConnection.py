import hub.SSERequest as SSERequest
import json
import sseclient
import time
import requests
import hub.Async as Async

class HubConnection:

    url = 'http://172.26.186.177/gap/nodes?event=1&mac=CC:1B:E0:E0:69:B0'
    urlConnectPrefix = 'http://172.26.186.177/gap/nodes/'
    urlConnectSuffix = '/connection?mac=CC:1B:E0:E0:69:B0'

    call_back = 0
    scanned_device_list = {}
    remove_list = []
    serial = 0
    last_serial = 0

    def __init__(self):
        self.serial = 0
        self.last_serial = self.serial
        thread = Async.Thread(self.start_event)
        thread.start()

    def data_listener(self):
        while True:
            self.remove_timeout_device()

            if self.serial > self.last_serial:
                self.last_serial = self.serial

            yield self.scanned_device_list

    def start_event(self):
        response = SSERequest.with_urllib3(self.url)
        client = sseclient.SSEClient(response)
        for event in client.events():
            scan_time = time.time()
            device_info_json = json.loads(event.data)
            name = device_info_json.get("name", "")
            if name == 'bong Vogue':
                mac = device_info_json.get("bdaddrs", "")[0]['bdaddr']
                device = {'name': name, "scan_time": scan_time}
                if mac not in self.scanned_device_list:
                    self.scanned_device_list[mac] = device
                    self.serial += 1
                    # self.call_back(self.scanned_device_list)
                else:
                    self.scanned_device_list[mac] = device

    def remove_timeout_device(self):
        has_changes = False

        for item in self.scanned_device_list:
            if self.scanned_device_list.get(item)['scan_time'] < time.time() - 5:
                self.remove_list.append(item)
                has_changes = True

        for item in self.remove_list:
            self.scanned_device_list.pop(item)

        self.remove_list = []

        return has_changes

    def connectDevice(self, mac):
        url = self.urlConnectPrefix + mac + self.urlConnectSuffix
        r = requests.post(url)
        if r.status_code == 200:
            return True
        else:
            return False

    def disconnectDevice(self, mac):
        url = self.urlConnectPrefix + mac + self.urlConnectSuffix
        r = requests.delete(url)
        if r.status_code == 200:
            return True
        else:
            return False
