# TagToInfo

TagToInfo is a desktop application built with PyQt5 that retrieves device information from a JAMF API endpoint and displays it to the user. The user enters a unique identifier such as a serial number, name or asset number for a device, and the application retrieves and displays the device's model, name, serial number, and management status.

Optionally, the application can automatically generate a QR code with this information and print it out.

## Dependencies

This application requires the following dependencies to be installed:

-   Python 3.11
-   PyQt5
-   requests
-   Pillow
-   qrcode

## Usage

1. Clone the repository.
2. Install the required packages using pip: `pip install -r requirements.txt`
3. Open the terminal and navigate to the cloned repository directory.
4. Run the application using the command `python3 main.py`.

## Configuration

Before running the application, you will need to provide your JAMF API credentials. These credentials are stored in a keychain, use python `keyring` to set them:

```python
import keyring

# jamf api
keyring.set_password("jamfcloud_api", "<username>", "<password>")

# helpdesk printer api
keyring.set_password("helpdesk_printer", "", "<key>")

# double check:
# jamf_api_user = "fresh-printer"
# print(keyring.get_password("jamfcloud_api", jamf_api_user))
# print(keyring.get_password("helpdesk_printer", ""))
```

Replace `username`, `password`, and `key` with your own credentials.
