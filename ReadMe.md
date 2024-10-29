# SteelSeries Rival 650 Wireless Battery Monitor

![Python](https://img.shields.io/badge/python-3.x-blue.svg)

## Description

This Python script allows users to monitor the battery level of the SteelSeries Rival 650 Wireless mouse. It utilizes
the `hid` library to communicate with the device and retrieves battery information through HID reports. The script opens
a connection to the mouse, sends a command to request the battery level, and processes the response to determine both
the battery percentage and the charging status.

## Features

- Retrieve the battery level of the SteelSeries Rival 650 Wireless mouse.
- Displays the current charging status of the device.
- Utilizes the HID protocol for communication with the device.

## Requirements

- Python 3.x
- `hidapi` library (can be installed via pip)
- `pystray` library (can be installed via pip)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ugurcandede/SteelSeries-Rival-650-Battery-Monitor.git
cd SteelSeries-Rival-650-Battery-Monitor
```

2. Install required libraries:

```bash
pip install -r requirements.txt
```

## Usage

Run the script to check the battery status of the connected SteelSeries Rival 650 Wireless mouse. An icon will be
displayed in the system tray.

```bash
python main.py
```

## Output

The main script executed an icon will be displayed in the system tray.

Otherwise, if `_init.py` is executed, will output the battery percentage and the charging status of the device. The
output will be as follows:

```
SteelSeries Rival 650 Wireless (wired mode) | 75% and it is charging
SteelSeries Rival 650 Wireless (2.4GHz wireless mode) | 50% and is not charging
```