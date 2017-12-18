import hub.SSERequest as SSERequest
import json
import sseclient
import time
import requests
import hub.Async as Async
import threading

class HubConnection:

    innerIP = '172.26.186.177'
    hubMac = 'CC:1B:E0:E0:69:B0'
    wristBandName = 'bong Vogue'

    urlScanDevices = 'http://' + innerIP + '/gap/nodes?event=1&mac=' + hubMac
    urlNotification = 'http://' + innerIP + '/gatt/nodes?mac=' + hubMac

    urlConnectPrefix = 'http://' + innerIP + '/gap/nodes/'
    urlConnectSuffix = '/connection?mac=' + hubMac
    urlConnectedList = 'http://' + innerIP + '/gap/nodes?connection_state=connected&mac=' + hubMac

    urlSetValueP1 = 'http://' + innerIP + '/gatt/nodes/'
    urlSetValueP2Option = '/handle/12/value/'
    urlSetValueP2 = '/handle/14/value/'
    urlSetValueP3 = '/?mac=' + hubMac

    call_back = 0
    scanned_device_list = {}
    remove_list = []
    serial = 0
    last_serial = 0

    start_measure_heart_time_dict = {}
    read_heart_rate_thread_dict = {}

    heart_rate_callback = None

    def __init__(self, heart_rate_callback):
        self.serial = 0
        self.last_serial = self.serial
        self.heart_rate_callback = heart_rate_callback
        thread_scan = Async.Thread(self.start_event)
        thread_scan.start()
        thread_receive_notification = Async.Thread(self.start_notify)
        thread_receive_notification.start()

    def data_listener(self):
        while True:
            self.remove_timeout_device()

            if self.serial > self.last_serial:
                self.last_serial = self.serial

            yield self.scanned_device_list

    def start_event(self):
        response = SSERequest.with_urllib3(self.urlScanDevices)
        client = sseclient.SSEClient(response)
        for event in client.events():
            scan_time = time.time()
            device_info_json = json.loads(event.data)
            name = device_info_json.get("name", "")
            if name == self.wristBandName:
                mac = device_info_json.get("bdaddrs", "")[0]['bdaddr']
                device = {'name': name, "scan_time": scan_time}
                if mac not in self.scanned_device_list:
                    self.scanned_device_list[mac] = device
                    self.serial += 1
                else:
                    self.scanned_device_list[mac] = device

    def start_notify(self):
        response = SSERequest.with_urllib3(self.urlNotification)
        client = sseclient.SSEClient(response)
        for event in client.events():
            notification = json.loads(event.data)
            value = notification.get('value', '')
            if(value.find("020101") != -1):
                mac = notification.get('id', '')
                if mac != '':
                    heart_rate = int(value[6:], 16)
                    return_obj = {'mac': mac, 'heart_rate': heart_rate}
                    self.heart_rate_callback(return_obj)

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
            # self.openWristBandNotify(mac)
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

    def openWristBandNotify(self, mac):
        url = self.urlSetValueP1 + mac + self.urlSetValueP2Option + '0100' + self.urlSetValueP3
        print(url)
        r = requests.post(url)
        if r.status_code == 200:
            return True
        else:
            return False

    def getConnectedDeviceList(self):
        url = self.urlConnectedList
        r = requests.get(url)
        if r.status_code == 200:
            record_device_list = {}
            jsonData = r.json()
            for node in jsonData.get('nodes'):
                mac = node['id']
                device = {'name': self.wristBandName}
                record_device_list[mac] = device
            return record_device_list
        return {}

    def startMeasureHeartRate(self, mac):
        start_time = int(time.time())
        print(start_time)
        time_in_hex = hex(start_time)[2:].upper()
        value_to_pass = '2900000015' + '01' + '13' + time_in_hex + '0000000000000000'
        print('time in hex : ' + time_in_hex)
        print('start pass value : ' + value_to_pass)
        url = self.urlSetValueP1 + mac + self.urlSetValueP2 + value_to_pass + self.urlSetValueP3
        self.start_measure_heart_time_dict[mac] = start_time
        requests.get(url)

        thread_read_heart_rate = threading.Thread(target=self.periodReadHeartRate, args=(mac, 5,))
        self.read_heart_rate_thread_dict[mac] = thread_read_heart_rate
        thread_read_heart_rate.start()

    def stopMeasureHeartRate(self, mac):
        start_time = self.start_measure_heart_time_dict.get(mac, int(time.time()))
        print(start_time)
        time_in_hex = hex(start_time)[2:].upper()
        value_to_pass = '2900000015' + '00' + '13' + time_in_hex + '0000000000000000'
        print('stop pass value : ' + value_to_pass)
        url = self.urlSetValueP1 + mac + self.urlSetValueP2 + value_to_pass + self.urlSetValueP3
        self.start_measure_heart_time_dict.pop(mac, None)
        requests.get(url)

        thread_read_heart_rate = self.read_heart_rate_thread_dict.get(mac, None)
        if thread_read_heart_rate != None:
            thread_read_heart_rate.keep_running = False

    def readHeartRate(self, mac):
        url = self.urlSetValueP1 + mac + self.urlSetValueP2 + '2600000052' + self.urlSetValueP3
        requests.get(url)

    def periodReadHeartRate(self, mac, periodSec):
        t = threading.currentThread()
        while getattr(t, "keep_running", True):
            self.readHeartRate(mac)
            time.sleep(periodSec)



