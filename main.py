import os
import sys
import json
import qrcode
import requests
from PIL import Image, ImageDraw, ImageFont
from PyQt5 import QtWidgets


class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Set window title, size, and widgets
        self.setWindowTitle("TagToInfo")
        self.setFixedSize(400, 280)
        self.asset_label = QtWidgets.QLabel(
            "Enter Unique Identifier (S/N, Name, Asset #):")
        self.asset_entry = QtWidgets.QLineEdit()
        self.print_var = QtWidgets.QCheckBox("Automatic Print")
        self.switch_label = QtWidgets.QLabel("Select Device Type:")
        self.switch_button = QtWidgets.QPushButton("Computer")
        self.status_label = QtWidgets.QLabel()
        self.model_label = QtWidgets.QLabel()
        self.name_label = QtWidgets.QLabel()
        self.serial_label = QtWidgets.QLabel()
        self.managed_label = QtWidgets.QLabel()
        self.copy_button = QtWidgets.QPushButton("Copy Serial Number")

        # Connect widgets to functions
        self.asset_entry.returnPressed.connect(self.submit_asset_request)
        self.copy_button.clicked.connect(self.copy_serial_number)
        self.switch_button.clicked.connect(self.switch_device_type)

        # Default button state and label text
        self.copy_button.setEnabled(False)
        self.copy_button.setText("Copy Serial Number")

        # Create layout and add widgets
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.asset_label)
        layout.addWidget(self.asset_entry)
        layout.addWidget(self.switch_label)
        layout.addWidget(self.switch_button)
        layout.addWidget(self.print_var)
        layout.addWidget(self.status_label)
        layout.addWidget(self.model_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.serial_label)
        layout.addWidget(self.managed_label)
        layout.addWidget(self.copy_button)

        # Load credentials from json file
        with open('/Users/Shared/secrets.json') as f:
            data = json.load(f)
            self.api_user = data['api_user']
            self.api_password = data['api_password']
            self.api_token = 'Bearer ' + data['api_token']
        self.api_endpoint = "https://wdm.jamfcloud.com/JSSResource"

        # Set default device type to computer
        self.device_type = "computer"
        self.switch_button.setText("Computer")

    def switch_device_type(self):
        # Toggle device type between computer and mobile device
        if self.device_type == "computer":
            self.device_type = "mobile device"
            self.switch_button.setText("Mobile Device")
        else:
            self.device_type = "computer"
            self.switch_button.setText("Computer")

    def submit_asset_request(self):
        # Get asset tag from widget
        asset_tag = self.asset_entry.text()
        self.copy_button.setText("Copy Serial Number")

        try:
            if self.device_type == "computer":
                # Get computer information from JAMF API
                name, serial, model, managed, jamf_url = self.get_computer_info(
                    asset_tag)
            else:
                # Get mobile device information from JAMF API
                name, serial, model, managed, jamf_url = self.get_mobiledevice_info(
                    asset_tag)

            # Set widget labels with device information
            self.status_label.setStyleSheet("color: green")
            self.status_label.setText(f"Request Successful")
            self.model_label.setText(f"Model: {model}")
            self.name_label.setText(f"Name: {name}")
            self.serial_label.setText(f"Serial Number: {serial}")
            self.managed_label.setText(f"Managed: {managed}")
            self.copy_button.setEnabled(True)

            # Generate computer information image if checkbox is checked
            if self.print_var.isChecked():
                self.generate_info(asset_tag, name, serial,
                                   model, jamf_url)
                self.print_asset_label()

        except ValueError as e:
            # Display error message if there is a problem with the input or API
            self.status_label.setText(f"Request Failed\n{e}")
            self.status_label.setStyleSheet("color: red")
            self.model_label.clear()
            self.name_label.clear()
            self.serial_label.clear()
            self.managed_label.clear()
            self.copy_button.setEnabled(False)

        # Clear asset entry widget after submitting request
        self.asset_entry.clear()

    def get_computer_info(self, asset_tag):
        # Setup JAMF API request and headers
        auth = self.api_user, self.api_password
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
        match_api_endpoint = f"{self.api_endpoint}/computers/match/{asset_tag}"

        # Get computer information from JAMF API and parse response
        response = requests.get(
            match_api_endpoint, headers=headers, auth=auth, verify=False)
        if response.status_code != 200:
            raise ValueError("Failed to connect to JAMF API")
        computer_match = json.loads(response.text)
        if "computers" not in computer_match or len(computer_match["computers"]) == 0:
            raise ValueError(f"Invalid asset ID")
        computer_id = computer_match["computers"][0]["id"]
        info_api_endpoint = f"{self.api_endpoint}/computers/id/{computer_id}"
        response = requests.get(
            info_api_endpoint, headers=headers, auth=auth, verify=False)
        computer = json.loads(response.text)["computer"]
        model = computer["hardware"]["model"]
        name = computer["general"]["name"]
        serial = computer["general"]["serial_number"]
        managed = computer["general"]["remote_management"]["managed"]
        jamf_url = f"https://wdm.jamfcloud.com/computers.html?id={computer_id}"

        # Return computer information
        return name, serial, model, managed, jamf_url

    def get_mobiledevice_info(self, asset_tag):
        # Setup JAMF API request and headers
        auth = self.api_user, self.api_password
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
        match_api_endpoint = f"{self.api_endpoint}/mobiledevices/match/{asset_tag}"

        # Get mobiledevice information from JAMF API and parse response
        response = requests.get(
            match_api_endpoint, headers=headers, auth=auth, verify=False)
        if response.status_code != 200:
            raise ValueError("Failed to connect to JAMF API")
        mobiledevice_match = json.loads(response.text)
        if "mobile_devices" not in mobiledevice_match or len(mobiledevice_match["mobile_devices"]) == 0:
            raise ValueError(f"Invalid asset ID")
        mobiledevice_id = mobiledevice_match["mobile_devices"][0]["id"]
        info_api_endpoint = f"{self.api_endpoint}/mobiledevices/id/{mobiledevice_id}"
        response = requests.get(
            info_api_endpoint, headers=headers, auth=auth, verify=False)
        mobiledevice = json.loads(response.text)["mobile_device"]
        model = mobiledevice["general"]["model"]
        name = mobiledevice["general"]["name"]
        serial = mobiledevice["general"]["serial_number"]
        managed = mobiledevice["general"]["managed"]
        jamf_url = f"https://wdm.jamfcloud.com/mobileDevices.html?id={mobiledevice_id}"

        # Return mobiledevice information
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

    def print_asset_label(self):
        # Print image to network printer
        asset_tag = self.asset_entry.text()
        headers = {'Authorization': f'{self.api_token}'}
        files = {'file': open(f'/tmp/tmp.upload-{asset_tag}.png', 'rb')}

        try:
            response = requests.post(
                'http://172.19.10.12:5001/print_image', headers=headers, files=files)
            data = response.json()
            if response.status_code == 200:
                self.status_label.setText(
                    f"Request Successful: {data['status']}")
                self.status_label.setStyleSheet("color: green")
            else:
                raise ValueError(f"Failed to print?")
        except:
            raise ValueError(f"Failed to connect to printer")

        # Remove temporary file after printing
        os.remove(f'/tmp/tmp.upload-{asset_tag}.png')

    def clear_asset_entry(self):
        # Clear asset entry and widget labels
        self.asset_entry.setText("")
        self.status_label.setText("")
        self.model_label.setText("")
        self.name_label.setText("")
        self.serial_label.setText("")


if __name__ == "__main__":
    # Create and show application window
    app = QtWidgets.QApplication([])
    window = App()
    window.show()
    sys.exit(app.exec_())
