# SteelSeries Rival 650 Wireless Battery Monitor

![Python](https://img.shields.io/badge/python-3.x-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A lightweight system tray application that monitors the battery level of your SteelSeries Rival 650 Wireless gaming mouse. Get real-time updates on battery percentage and charging status without interrupting your workflow.

## Features

- 🔋 Real-time battery level monitoring
- 🔌 Charging status indication
- 💻 System tray integration
- 🎮 Support for both wired and wireless (2.4GHz) modes
- 🚀 Minimal resource usage
- 🔄 Automatic updates

## Prerequisites

- Python 3.x
- Windows operating system
- SteelSeries Rival 650 Wireless mouse

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ugurcandede/SteelSeries-Rival-650-Battery-Monitor.git
   cd SteelSeries-Rival-650-Battery-Monitor
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Recommended Method (Windows Executable)
Download and run the executable file from the [latest release](https://github.com/ugurcandede/SteelSeries-Rival-650-Battery-Monitor/releases/latest):
1. Download `Rival650BatteryMonitor.exe`
2. Double-click to run the application
3. The battery monitor will appear in your system tray

### Alternative Methods

#### System Tray Application (From Source)
Run the main application to get a system tray icon:
```bash
python main.py
```

The system tray icon will:
- Show battery percentage on hover
- Update automatically
- Provide quick access to common actions

#### Command Line Interface
For command-line battery status checks:
```bash
python _init.py
```

Example output:
```
SteelSeries Rival 650 Wireless (wired mode) | 75% and it is charging
SteelSeries Rival 650 Wireless (2.4GHz wireless mode) | 50% and is not charging
```

## Technical Details

The application uses the `hidapi` library to communicate with the mouse through HID (Human Interface Device) reports. It:
- Establishes a connection to the device
- Sends commands to request battery information
- Processes responses to determine battery level and charging status
- Updates the system tray icon accordingly

## Troubleshooting

1. **Mouse Not Detected**
   - Ensure the mouse is properly connected
   - Try unplugging and reconnecting the device
   - Check if the device appears in Windows Device Manager

2. **Permission Issues**
   - Run the application with administrator privileges
   - Verify user permissions for HID devices

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- SteelSeries for their excellent gaming hardware
- The `hidapi` and `pystray` library maintainers