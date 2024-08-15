from setuptools import setup
import subprocess

APP = ['main.py']
DATA_FILES = [('assets', ['assets/template.png',
               'assets/Arial.ttf', 'assets/Arial Bold.ttf'])]
OPTIONS = {
    'iconfile': 'assets/icon.icns',
    'plist': {
        'CFBundleName': 'TagToInfo',
        'CFBundleDisplayName': 'TagToInfo',
        'CFBundleIdentifier': 'com.woodleigh.tagtoinfo',
        'CFBundleVersion': '2.1',
        'CFBundleShortVersionString': '2',
    },
    'packages': ['keyring', 'requests', 'qrcode', 'PyQt5', 'PIL'],
    'includes': ['sys', 'os'],
}

setup(
    app=APP,
    name='TagToInfo',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

subprocess.run(['codesign', '--deep', '--signature-size', '9400', '-f', '-s', 'Developer ID Application: Woodleigh School (SMLKBTR495)', 'dist/TagToInfo.app'])
