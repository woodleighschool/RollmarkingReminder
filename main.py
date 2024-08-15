import os
import sys
import requests
import keyring
import qrcode
from PyQt5 import QtWidgets, QtCore
from PIL import Image, ImageDraw, ImageFont


class TagToInfo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.load_credentials()
        self.setup_ui()
        self.device_data = self.fetch_all_devices()

    def setup_ui(self):
        self.setWindowTitle('TagToInfo')
        self.setFixedSize(400, 400)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setup_widgets()
        self.connect_signals()

    def setup_widgets(self):
        self.asset_label = QtWidgets.QLabel('Enter Unique Device Identifier')
        self.asset_entry = QtWidgets.QLineEdit()
        self.asset_entry.setPlaceholderText('13233, SS-HYDEA22, FVFXN3Y6J1WT')
        self.device_list = QtWidgets.QListWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.device_list.setSizePolicy(size_policy)
        self.name_label = QtWidgets.QLabel()
        self.model_label = QtWidgets.QLabel()
        self.serial_label = QtWidgets.QLabel()
        self.processor_label = QtWidgets.QLabel()
        self.ram_label = QtWidgets.QLabel()
        self.storage_label = QtWidgets.QLabel()
        self.managed_label = QtWidgets.QLabel()
        self.copy_button = QtWidgets.QPushButton('Copy Serial Number')
        self.print_button = QtWidgets.QPushButton('Print Info')
        self.copy_button.setDisabled(True)
        self.print_button.setDisabled(True)
        widgets = [self.asset_label, self.asset_entry, self.device_list, self.name_label, self.model_label,
                   self.serial_label, self.processor_label, self.ram_label, self.storage_label, self.managed_label]
        for widget in widgets:
            self.layout.addWidget(widget)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.copy_button)
        hbox.addWidget(self.print_button)
        self.layout.addLayout(hbox)

    def connect_signals(self):
        self.asset_entry.textChanged.connect(self.search_devices)
        self.asset_entry.returnPressed.connect(self.on_return_pressed)
        self.device_list.itemClicked.connect(self.select_device)
        self.copy_button.clicked.connect(self.copy_serial_number)
        self.print_button.clicked.connect(self.print_label)

    def load_credentials(self):
        self.jamf_api_client_id = keyring.get_password('jamfcloud_api', 'client_id')
        self.jamf_api_client_secret = keyring.get_password('jamfcloud_api', 'client_secret')
        self.printer_api_key = 'Bearer ' + keyring.get_password('helpdesk_printer', '')

    def authenticate_jamf_api(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'client_id': self.jamf_api_client_id, 'client_secret': self.jamf_api_client_secret,
                'grant_type': 'client_credentials'}
        response = requests.post('https://wdm.jamfcloud.com/api/oauth/token', headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']

    def round_sizes(self, size_mb):
        if size_mb is None:
            return ''
        size_gb = size_mb / 1024
        if size_gb <= 512:
            sizes = [4, 8, 16, 24, 32, 36, 48, 64, 96, 128, 256, 512]
            for bracket in sizes:
                if size_gb <= bracket:
                    return f'{bracket}GB'
        else:
            size_tb = round(size_gb / 1024)
            if size_tb == 0:
                size_tb = 1
            tb_brackets = [1, 2, 4, 8]
            for bracket in tb_brackets:
                if size_tb <= bracket:
                    return f'{bracket}TB'
        return '8TB+'

    def fetch_all_devices(self):
        auth_token = self.authenticate_jamf_api()
        headers = {'Authorization': f'Bearer {auth_token}', 'Accept': 'application/json'}
        devices = {}
        devices.update(self.fetch_computers(headers))
        devices.update(self.fetch_mobile_devices(headers))
        return devices

    def fetch_computers(self, headers):
        url = 'https://wdm.jamfcloud.com/api/v1/computers-inventory?section=GENERAL&section=STORAGE&section=HARDWARE&page=0&page-size=5000&sort=general.name%3Aasc'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        computers = {}
        for item in data['results']:
            storage_megabytes = None
            for disk in item['storage']['disks']:
                if disk['device'] == 'disk0':
                    storage_megabytes = disk.get('sizeMegabytes')
                    break
            computers[f'computer_{item['id']}'] = {
                'name': item['general']['name'],
                'assetTag': item['general'].get('assetTag', ''),
                'model': item['hardware']['model'],
                'serialNumber': item['hardware']['serialNumber'],
                'storage': self.round_sizes(storage_megabytes),
                'processorType': item['hardware']['processorType'],
                'ram': self.round_sizes(item['hardware'].get('totalRamMegabytes')),
                'managed': item['general']['remoteManagement']['managed']
            }
        return computers

    def fetch_mobile_devices(self, headers):
        url = 'https://wdm.jamfcloud.com/api/v2/mobile-devices/detail?section=GENERAL&section=HARDWARE&page=0&page-size=5000&sort=displayName%3Aasc'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        mobile_devices = {}
        for item in data['results']:
            mobile_devices[f'mobile_{item['mobileDeviceId']}'] = {
                'name': item['general']['displayName'],
                'assetTag': item['general'].get('assetTag', ''),
                'model': item['hardware']['model'],
                'serialNumber': item['hardware']['serialNumber'],
                'storage': self.round_sizes(item['hardware'].get('capacityMb'))
            }
        return mobile_devices

    def search_devices(self, text):
        self.device_list.clear()
        if not text:
            return
        keys_to_search = ['assetTag', 'serialNumber', 'name']
        for device_id, device_info in self.device_data.items():
            for key in keys_to_search:
                if key in device_info and text.lower() in str(device_info[key]).lower():
                    item = QtWidgets.QListWidgetItem(f'{device_info[key]}')
                    if item is not None:
                        item.setData(QtCore.Qt.UserRole, device_id)
                        self.device_list.addItem(item)
                    break

    def select_device(self, item):
        self.device_id = item.data(QtCore.Qt.UserRole)
        device_info = self.device_data[self.device_id]
        self.update_ui_with_device_info(device_info)
        self.print_button.setDisabled(False)
        self.copy_button.setDisabled(False)
        self.copy_button.setText('Copy Serial Number')

    def update_ui_with_device_info(self, device_info):
        self.name_label.setText(f'<b>Name:</b> {device_info['name']}')
        self.model_label.setText(f'<b>Model:</b> {device_info['model']}')
        self.serial_label.setText(f'<b>Serial Number:</b> {device_info['serialNumber']}')
        self.processor_label.setText(f'<b>Processor:</b> {device_info.get('processorType', '')}')
        self.ram_label.setText(f'<b>RAM:</b> {device_info.get('ram', '')}')
        self.storage_label.setText(f'<b>Storage:</b> {device_info['storage']}')
        self.managed_label.setText(f'<b>Managed:</b> {device_info.get('managed', 'N/A')}')

    def print_label(self):
        if 'computer' in self.device_id:
            device_type = 'computers.html'
        else:
            device_type = 'mobileDevices.html'
        id_number = self.device_id.split('_')[1]
        jamf_url = f'https://wdm.jamfcloud.com/{device_type}?id={id_number}&o=r'
        data = [
            id_number,
            self.name_label.text().split(':')[1].strip().replace('</b>', '').strip(),
            self.serial_label.text().split(':')[1].strip().replace('</b>', '').strip(),
            self.model_label.text().split(':')[1].strip().replace('</b>', '').strip(),
            self.processor_label.text().split(':')[1].strip().replace('</b>', '').strip(),
            self.ram_label.text().split(':')[1].strip().replace('</b>', '').strip().split()[0] + 'GB',
            self.storage_label.text().split(':')[1].strip().replace('</b>', '').strip().split()[0] + 'GB',
            jamf_url
        ]
        self.generate_info(*data)
        self.print_asset_label(id_number)

    def generate_info(self, id_number, name, serial, model, processor, ram, storage, jamf_url):
        global_x = 566
        global_buffer = 10
        current_y = 170
        max_width = 596
        font_size = 48
        qr = qrcode.QRCode(version=1, box_size=16, border=0)
        qr.add_data(jamf_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='black', back_color='white')
        template_img = Image.open(os.path.join(os.path.dirname(__file__), 'assets/template.png'))
        template_img.paste(qr_img, (19, 19))
        draw = ImageDraw.Draw(template_img)
        font = ImageFont.truetype('assets/Arial.ttf', size=48)
        draw.text((global_x, current_y), f'Name: {name}', font=font, fill='black')
        current_y = current_y + 48 + global_buffer
        draw.text((global_x, current_y), f'Serial #: {serial}', font=font, fill='black')
        current_y = current_y + 48 + global_buffer
        draw.text((global_x, current_y), f'Specifications:', font=font, fill='black')
        current_y = current_y + 48 + global_buffer
        text_width = draw.textlength(model, font=font)
        while text_width > max_width:
            font_size -= 1
            font = ImageFont.truetype('assets/Arial.ttf', size=font_size)
            text_width = draw.textlength(model, font=font)
        draw.text((global_x, current_y), f'{processor}, {ram}/{storage}', font=font, fill='black')
        current_y = current_y + font_size + global_buffer
        draw.text((global_x, current_y), model, font=font, fill='black')
        info_image_path = f'/tmp/tmp.upload-{id_number}.png'
        template_img.save(info_image_path)

    def copy_serial_number(self):
        serial_number = self.serial_label.text().split(': ')[1]
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(serial_number)
        self.copy_button.setText('Copied!')

    def on_return_pressed(self):
        if self.device_list.count() == 1:
            item = self.device_list.item(0)
            self.select_device(item)

    def print_asset_label(self, id_number):
        headers = {'Authorization': f'{self.printer_api_key}'}
        files = {'file': open(f'/tmp/tmp.upload-{id_number}.png', 'rb')}
        try:
            requests.post('http://172.19.10.12:5001/print_image', headers=headers, files=files, timeout=5)
            self.print_button.setText('Print Successful!')
        except requests.exceptions.RequestException:
            self.print_button.setText('Failed to Connect to Printer!')
        finally:
            files['file'].close()
            os.remove(f'/tmp/tmp.upload-{id_number}.png')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = TagToInfo()
    window.show()
    sys.exit(app.exec_())
