# WPBot

WPBot is an automation bot for handling WhatsApp Web messages and attachments. It logs into WhatsApp Web, checks for new messages, processes attachments, and saves them to a specified directory.

## Features

- Automatically logs into WhatsApp Web using QR code scanning.
- Checks for new messages periodically.
- Processes image albums, single images, and document files.
- Moves and renames downloaded files to a target directory.
- Logs activities and handles errors gracefully.
- Compresses log files when they reach a specified limit.

## Requirements

- Python 3.11.9
- Google Chrome
- ChromeDriver compatible with your Chrome version

## Installation

### Python Installation

1. Download the `python-3.11.9-amd64.exe` file.
2. Start the installation process.
3. During installation, check the "Add Python to PATH" option.

### Installing Dependencies

1. Run the `requirements_installer.bat` file to install all necessary dependencies.

### Moving WPBot Folder

1. Move the WPBot folder to a secure location on your computer where it won't be deleted.

### Creating a Bot Starter Shortcut

1. Right-click on the `Bot_Starter.bat` file in the WPBot folder and create a shortcut on your desktop.
2. Use the shortcut on your desktop to start the bot.

## Usage

1. Ensure all installation steps have been completed.
2. Double-click the Bot Starter shortcut on your desktop.
3. Scan the QR code using your WhatsApp mobile app to log in.
4. The bot will now check for new messages and process any attachments automatically.

## Configuration

### LDAP Connection

Update the LDAP server information in the script:

'''py
ldap_server = "ldap://DOMAIN"
ldap_user = "DOMAIN\\USER"
ldap_password = "PASSWORD"
'''

### Target Directory

Set the target directory for saving files:

'''py
target_dir = "TARGET LOCATION"
'''

### ChromeDriver Path

Set the ChromeDriver path:

'''py
chrome_driver_path = "./chromedriver.exe"
'''

## Logging

- Logs are saved in the `WPBot Log` directory in your system's temporary folder.
- Log files are compressed when they reach the maximum number of lines specified.

