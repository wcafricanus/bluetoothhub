import json
import sseclient
import time
import requests
import hub.Async as Async
import threading
import base64


class HubConnection:
    def __init__(self, heart_rate_callback, config):
        self.config = config
        self.local = self.config['CONNECTION_MODE']
        if self.local:
            self.innerIP = self.config['HUB_IP_PRIVATE']
        else:
            self.innerIP = self.config['AC_IP'] + '/api'
        self.hubMac = 'CC:1B:E0:E0:69:B0'
        self.wristBandName = 'bong Vogue'

        self.urlScanDevices = 'http://' + self.innerIP + '/gap/nodes?event=1&mac=' + self.hubMac
        self.urlNotification = 'http://' + self.innerIP + '/gatt/nodes?mac=' + self.hubMac

        self.urlConnectPrefix = 'http://' + self.innerIP + '/gap/nodes/'
        self.urlConnectSuffix = '/connection?mac=' + self.hubMac
        self.urlConnectedList = 'http://' + self.innerIP + '/gap/nodes?connection_state=connected&mac=' + self.hubMac

        self.urlSetValueP1 = 'http://' + self.innerIP + '/gatt/nodes/'
        self.urlSetValueP2Option = '/handle/12/value/'
        self.urlSetValueP2 = '/handle/14/value/'
        self.urlSetValueP3 = '/?mac=' + self.hubMac

        self.call_back = 0
        self.scanned_device_list = {}
        self.remove_list = []
        self.serial = 0
        self.last_serial = 0

        self.start_measure_heart_time_dict = {}
        self.read_heart_rate_thread_dict = {}

        self.serial = 0
        self.last_serial = self.serial
        self.heart_rate_callback = heart_rate_callback
        self.token_receive_time = time.time()
        self.token_expires_in = 0
        self.token_header = {}

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
        response = self.request_get(self.urlScanDevices, stream=True)
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
        response = self.request_get(self.urlNotification, stream=True)
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
        r = self.request_post(url)
        if r.status_code == 200:
            return True
        else:
            return False

    def disconnectDevice(self, mac):
        url = self.urlConnectPrefix + mac + self.urlConnectSuffix
        r = self.request_delete(url)
        if r.status_code == 200:
            return True
        else:
            return False

    def openWristBandNotify(self, mac):
        url = self.urlSetValueP1 + mac + self.urlSetValueP2Option + '0100' + self.urlSetValueP3
        print(url)
        r = self.request_get(url)
        print(r.text)
        if r.status_code == 200:
            return True
        else:
            return False

    def getConnectedDeviceList(self):
        url = self.urlConnectedList
        r = self.request_get(url)
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
        self.openWristBandNotify(mac)

        start_time = int(time.time())
        print(start_time)
        time_in_hex = hex(start_time)[2:].upper()
        value_to_pass = '2900000015' + '01' + '13' + time_in_hex + '0000000000000000'
        print('time in hex : ' + time_in_hex)
        print('start pass value : ' + value_to_pass)
        url = self.urlSetValueP1 + mac + self.urlSetValueP2 + value_to_pass + self.urlSetValueP3
        self.start_measure_heart_time_dict[mac] = start_time
        self.request_get(url)

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
        self.request_get(url)

        thread_read_heart_rate = self.read_heart_rate_thread_dict.get(mac, None)
        if thread_read_heart_rate != None:
            thread_read_heart_rate.keep_running = False

    def readHeartRate(self, mac):
        url = self.urlSetValueP1 + mac + self.urlSetValueP2 + '2600000052' + self.urlSetValueP3
        self.request_get(url)

    def periodReadHeartRate(self, mac, periodSec):
        t = threading.currentThread()
        while getattr(t, "keep_running", True):
            self.readHeartRate(mac)
            time.sleep(periodSec)

    def request_get(self, url, params=None, **kwargs):
        self.ensure_header_with_token(kwargs)
        return requests.get(url, params, **kwargs)

    def request_post(self, url, data=None, json=None, **kwargs):
        self.ensure_header_with_token(kwargs)
        return requests.post(url, data=data, json=json, **kwargs)

    def request_delete(self, url, **kwargs):
        self.ensure_header_with_token(kwargs)
        return requests.delete(url, **kwargs)

    def ensure_valid_token(self):
        if time.time() < self.token_receive_time + self.token_expires_in:
            return self.token_header
        self.request_token()

    def ensure_header_with_token(self, kwargs):
        if self.local:
            return # Do nothing in local mode
        self.ensure_valid_token()
        if not kwargs.get('headers'):
            kwargs['headers'] = self.token_header
        else:
            kwargs['headers'].update(self.token_header)

    def request_token(self):
        self.token_receive_time = time.time()
        url = 'http://' + self.innerIP + '/oauth2/token'
        string_to_encode = self.config['DEVELOPER_ID'] + ':' + self.config['SECRET'];
        encoded_string = base64.b64encode(string_to_encode.encode())
        data = {'grant_type' : 'client_credentials'}
        headers = {
            'Authorization': 'Basic ' + encoded_string.decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(url=url, data=data, headers=headers)
        response_dict = response.json()
        access_token = response_dict['access_token']
        self.token_expires_in = response_dict['expires_in']
        self.token_header = {'Authorization' : 'Bearer ' + access_token}