import os
import sys
import json
import qrcode
import requests
import keyring
from PIL import Image, ImageDraw, ImageFont
from PyQt5 import QtWidgets


class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Set window title, size, and widgets
        self.setWindowTitle("TagToInfo")
        self.setFixedSize(400, 300)
        self.asset_label = QtWidgets.QLabel(
            "Enter Unique Identifier (S/N, Name, Asset #):")
        self.asset_entry = QtWidgets.QLineEdit()
        self.print_var = QtWidgets.QCheckBox("Automatic Print")
        self.force_print_button = QtWidgets.QPushButton("Print Anyway")
        self.status_label = QtWidgets.QLabel()
        self.model_label = QtWidgets.QLabel()
        self.name_label = QtWidgets.QLabel()
        self.serial_label = QtWidgets.QLabel()
        self.managed_label = QtWidgets.QLabel()
        self.copy_button = QtWidgets.QPushButton("Copy Serial Number")

        # Connect widgets to functions
        self.asset_entry.returnPressed.connect(self.submit_asset_request)
        self.copy_button.clicked.connect(self.copy_serial_number)
        self.force_print_button.clicked.connect(self.force_print)

        # Default button state and label text
        self.copy_button.setEnabled(False)
        self.force_print_button.setEnabled(False)
        self.copy_button.setText("Copy Serial Number")

        # Create layout and add widgets
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.asset_label)
        layout.addWidget(self.asset_entry)

        # Create a horizontal layout for checkbox and button
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.print_var)
        hbox.addWidget(self.force_print_button)
        hbox.addStretch()

        layout.addLayout(hbox)

        layout.addWidget(self.status_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.model_label)
        layout.addWidget(self.serial_label)
        layout.addWidget(self.managed_label)
        layout.addWidget(self.copy_button)

        # Load credentials keychain
        self.jamf_api_user = "fresh-printer"
        self.jamf_api_password = keyring.get_password("jamfcloud_api", self.jamf_api_user)
        self.printer_api_key = 'Bearer ' + keyring.get_password("helpdesk_printer", "")
        self.jamf_api_endpoint = "https://wdm.jamfcloud.com/JSSResource"

    def force_print(self):
        previous_submit = self.status_label.text().split(": ")[1]
        force_print = True
        self.submit_asset_request(previous_submit, force_print)

    def submit_asset_request(self, previous_submit=None, force_print=False):
        # Get asset tag from widget or use the previous_submit if provided
        asset_tag = previous_submit if previous_submit else self.asset_entry.text()
        self.copy_button.setText("Copy Serial Number")
        self.force_print_button.setText("Print Anyway")

        try:
            # Get computer information from JAMF API
            name, serial, model, managed, jamf_url = self.get_device_info(
                asset_tag)

            # Set widget labels with device information
            self.status_label.setStyleSheet("color: green")
            self.status_label.setText(f"Showing results for: {asset_tag}")
            self.model_label.setText(f"Model: {model}")
            self.name_label.setText(f"Name: {name}")
            self.serial_label.setText(f"Serial Number: {serial}")
            self.managed_label.setText(f"Managed: {managed}")
            self.copy_button.setEnabled(True)
            self.force_print_button.setEnabled(True)

            # Generate computer information image if checkbox is checked or force_print is True
            if self.print_var.isChecked() or force_print:
                self.generate_info(asset_tag, name, serial,
                                   model, jamf_url)
                self.print_asset_label(asset_tag)

        except ValueError as e:
            # Display error message if there is a problem with the input or API
            self.status_label.setText(f"{e}")
            self.status_label.setStyleSheet("color: red")
            self.model_label.clear()
            self.name_label.clear()
            self.serial_label.clear()
            self.managed_label.clear()
            self.copy_button.setEnabled(False)
            self.force_print_button.setEnabled(False)

        # Clear asset entry widget after submitting request
        self.asset_entry.clear()

    def get_device_info(self, asset_tag):
        # Setup JAMF API request and headers
        auth = self.jamf_api_user, self.jamf_api_password
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}

        # Try to match computer first
        match_jamf_api_endpoint = f"{self.jamf_api_endpoint}/computers/match/{asset_tag}"
        response = requests.get(
            match_jamf_api_endpoint, headers=headers, auth=auth, verify=False)
        if response.status_code != 200:
            raise ValueError("Failed to connect to JAMF API")

        device_match = json.loads(response.text)

        if "computers" in device_match and len(device_match["computers"]) > 0:
            device_type = "computers"
            device_id = device_match["computers"][0]["id"]
        else:
            # If not matched as computer, try mobiledevice
            match_jamf_api_endpoint = f"{self.jamf_api_endpoint}/mobiledevices/match/{asset_tag}"
            response = requests.get(
                match_jamf_api_endpoint, headers=headers, auth=auth, verify=False)
            if response.status_code != 200:
                raise ValueError("Failed to connect to JAMF API")

            device_match = json.loads(response.text)
            if "mobile_devices" in device_match and len(device_match["mobile_devices"]) > 0:
                device_type = "mobiledevices"
                device_id = device_match["mobile_devices"][0]["id"]
            else:
                raise ValueError(f"Could not match \"{asset_tag}\"")

        # Get device information from JAMF API and parse response
        info_jamf_api_endpoint = f"{self.jamf_api_endpoint}/{device_type}/id/{device_id}"
        response = requests.get(
            info_jamf_api_endpoint, headers=headers, auth=auth, verify=False)

        if device_type == "computers":
            computer = json.loads(response.text)["computer"]
            model = computer["hardware"]["model"]
            name = computer["general"]["name"]
            serial = computer["general"]["serial_number"]
            managed = computer["general"]["remote_management"]["managed"]
            jamf_url = f"https://wdm.jamfcloud.com/computers.html?id={device_id}"
        else:
            mobiledevice = json.loads(response.text)["mobile_device"]
            model = mobiledevice["general"]["model"]
            name = mobiledevice["general"]["name"]
            serial = mobiledevice["general"]["serial_number"]
            managed = mobiledevice["general"]["managed"]
            jamf_url = f"https://wdm.jamfcloud.com/mobileDevices.html?id={device_id}"

        # Return device information
        return name, serial, model, managed, jamf_url

    def generate_info(self, asset_tag, name, serial, model, jamf_url):
        # Generate QR code with JAMF API url
        qr = qrcode.QRCode(version=1, box_size=16, border=0)
        qr.add_data(jamf_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Generate image of computer information with QR code
        template_img = Image.open(os.path.join(
            os.path.dirname(__file__), 'assets/template.png'))
        template_img.paste(qr_img, (19, 19))
        draw = ImageDraw.Draw(template_img)
        font_heading = ImageFont.truetype('assets/Arial Bold.ttf', size=48)
        font_data = ImageFont.truetype('assets/Arial.ttf', size=48)

        # Add computer information to image
        draw.text((566, 168), f'Name:', font=font_heading, fill='black')
        draw.text((566, 288), f'Serial Number:',
                  font=font_heading, fill='black')
        draw.text((566, 419), f'Model:', font=font_heading, fill='black')
        draw.text((566, 342), f'{serial}', font=font_data, fill='black')

        # Resize font if name or model length is too long
        name_bbox = font_data.getbbox(name)
        name_width = name_bbox[2] - name_bbox[0]
        if name_width > 596:
            while name_width > 596:
                font_data = ImageFont.truetype(
                    'assets/Arial.ttf', size=font_data.size - 1)
                name_bbox = font_data.getbbox(name)
                name_width = name_bbox[2] - name_bbox[0]
        draw.text((566, 222), f'{name}', font=font_data, fill='black')

        model_bbox = font_data.getbbox(model)
        model_width = model_bbox[2] - model_bbox[0]
        if model_width > 596:
            while model_width > 596:
                font_data = ImageFont.truetype(
                    'assets/Arial.ttf', size=font_data.size - 1)
                model_bbox = font_data.getbbox(model)
                model_width = model_bbox[2] - model_bbox[0]
        draw.text((566, 471), f'{model}', font=font_data, fill='black')

        # Save image to temporary file
        info_image_path = f'/tmp/tmp.upload-{asset_tag}.png'
        template_img.save(info_image_path)

    def copy_serial_number(self):
        # Copy serial number to clipboard when copy button is clicked
        serial_number = self.serial_label.text().split(": ")[1]
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(serial_number)
        self.copy_button.setText("Copied!")

    def print_asset_label(self, asset_tag):
        # Print image to network printer
        headers = {'Authorization': f'{self.printer_api_key}'}
        files = {'file': open(f'/tmp/tmp.upload-{asset_tag}.png', 'rb')}

        try:
            requests.post('http://172.19.10.12:5001/print_image',
                          headers=headers, files=files, timeout=5)
            self.force_print_button.setText("Sent to print")
        except requests.exceptions.RequestException:
            self.force_print_button.setText("Failed to print!")
        finally:
            files['file'].close()
            os.remove(f'/tmp/tmp.upload-{asset_tag}.png')


if __name__ == "__main__":
    # Create and show application window
    app = QtWidgets.QApplication([])
    window = App()
    window.show()
    sys.exit(app.exec_())
