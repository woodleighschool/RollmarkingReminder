#!/usr/local/bin/python3
from setuptools import setup
import subprocess
import shutil
import os
import glob

APP = ['main.py']
OPTIONS = {
    'iconfile': 'assets/icon.icns',
    'argv_emulation': True,
    'plist': {
        'CFBundleName': 'RollMarkingReminder',
        'CFBundleDisplayName': 'Roll Marking Reminder',
        'CFBundleIdentifier': 'au.edu.vic.woodleigh.rollmarkingreminder',
        'CFBundleVersion': '2.0',
        'CFBundleShortVersionString': '2',
        'LSBackgroundOnly': True,
    },
    'packages': ['desktop_notifier'],
    'includes': ['asyncio', 'time', 'datetime', 're', 'subprocess'],
    'excludes': ['rubicon']
}

def copy_rubicon():
    """
    Manually copy `rubicon` and its metadata to the py2app build directory.
    """
    # Source directories
    rubicon_src = '/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/rubicon'
    dist_info_src = '/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/rubicon_objc-*.dist-info'
    
    # Destination directory
    dest_dir = 'dist/RollMarkingReminder.app/Contents/Resources/lib/python3.12'
    
    # Ensure the destination directory exists
    os.makedirs(dest_dir, exist_ok=True)
    
    # Copy the `rubicon` directory
    if os.path.exists(rubicon_src):
        shutil.copytree(rubicon_src, os.path.join(dest_dir, 'rubicon'), dirs_exist_ok=True)
        print(f"Copied {rubicon_src} to {dest_dir}")
    else:
        print(f"Error: Source directory {rubicon_src} not found.")
    
    # Copy the `rubicon_objc-*.dist-info` directory
    for dist_info in glob.glob(dist_info_src):
        shutil.copytree(dist_info, os.path.join(dest_dir, os.path.basename(dist_info)), dirs_exist_ok=True)
        print(f"Copied {dist_info} to {dest_dir}")

setup(
    app=APP,
    name='RollMarkingReminder',
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

copy_rubicon()

subprocess.run(['codesign', '--deep', '--signature-size', '9400', '-f', '-s', 'Developer ID Application: Woodleigh School (SMLKBTR495)', 'dist/RollMarkingReminder.app'])
