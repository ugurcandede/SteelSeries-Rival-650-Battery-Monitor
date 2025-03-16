#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Ugurcan Dede
Date: 2024-10-28
GitHub: https://github.com/ugurcandede

SteelSeries Rival 650 Battery Monitor - System Tray Application

This script creates a system tray icon that displays the battery level of a SteelSeries Rival 650 Wireless mouse.
It provides real-time monitoring of the battery status and charging state through a graphical interface.
"""

import threading
import time
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from pystray import Icon, MenuItem, Menu

from _init import DeviceManager, BatteryStatus, DeviceStatus, DeviceNotFoundError

# Constants
REFRESH_TIMEOUT = 5  # Regular refresh interval in seconds
ERROR_RETRY_TIMEOUT = 3  # Retry interval when error occurs in seconds
POLLING_INTERVAL = 1 / 20  # Polling interval for device detection

# UI Constants
ICON_SIZE = (50, 50)
ICON_BG_COLOR = (255, 255, 255, 90)
FONT_SIZE = 31
FONT_NAME = "arial.ttf"
FONT_COLOR = "white"

# Battery Level Thresholds
BATTERY_HIGH = 75
BATTERY_MEDIUM = 30

# Battery Level Colors and Positions
BATTERY_LEVELS = {
    "high": ("green", 0),
    "medium": ("orange", 25),
    "low": ("red", 40),
    "unknown": ("purple", 0)
}

class DeviceConnectionError(Exception):
    """Raised when there are issues connecting to the device."""
    pass

class SystrayIcon:
    def __init__(self):
        self.device_manager: DeviceManager = DeviceManager()
        self.battery_status: BatteryStatus = BatteryStatus(self.device_manager)
        self.last_update: Optional[float] = None
        self.battery_level: Optional[int] = None
        self.battery_charging: Optional[bool] = None
        self.systray_icon: Optional[Icon] = None
        self.stopped: bool = False
        self.event: threading.Event = threading.Event()

    def create_menu(self, name: str) -> Menu:
        """Create the system tray menu with current device status."""
        return Menu(
            MenuItem(f"Name: {name}", lambda: None, enabled=False),
            MenuItem(
                f"Battery: {f'{self.battery_level}%' if self.battery_level is not None else 'N/A'}", 
                lambda: None, 
                enabled=False
            ),
            MenuItem(
                f"Status: {'Charging' if self.battery_charging else 'Discharging'}", 
                lambda: None, 
                enabled=False
            ),
            MenuItem(
                f"Last update: {time.strftime('%H:%M:%S', time.localtime(self.last_update))} (click to refresh)", 
                self.refresh_connection
            ),
            MenuItem("Quit", self.quit_app)
        )

    def get_battery(self) -> None:
        """Monitor battery status in a continuous loop."""
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while not self.stopped:
            try:
                device = self.device_manager.exists_model
                if device is None:
                    raise DeviceConnectionError("No device found")

                device_name = device['name']
                
                # Try to verify device access before proceeding
                if not self.device_manager.verify_device_access(
                    device['vendor_id'], 
                    device['product_id'], 
                    device['endpoint']
                ):
                    raise DeviceConnectionError(f"Device {device_name} found but cannot be accessed")
                
                print(f"{time.strftime('%H:%M:%S')} | Mouse found and accessible: {device_name}")
                
                battery = self.battery_status.get_status()
                
                if battery['name'] == "No device found":
                    if consecutive_failures >= max_consecutive_failures:
                        self._handle_dongle_only_state(device_name)
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        print(f"Failed to read battery status (attempt {consecutive_failures}/{max_consecutive_failures})")
                        time.sleep(POLLING_INTERVAL)
                    continue

                # Reset failure counter on successful read
                consecutive_failures = 0
                self.update_battery_info(battery)

                sleep_time = REFRESH_TIMEOUT if self.battery_level is not None else POLLING_INTERVAL
                self.event.clear()
                self.event.wait(timeout=sleep_time)

            except DeviceConnectionError as e:
                self._handle_error_state(f"Connection error: {str(e)}")
                time.sleep(ERROR_RETRY_TIMEOUT)
                self.refresh_connection()
            except DeviceNotFoundError as e:
                self._handle_error_state(f"Device error: {str(e)}")
                time.sleep(ERROR_RETRY_TIMEOUT)
                self.refresh_connection()
            except Exception as e:
                self._handle_error_state(f"Unexpected error: {str(e)}")
                time.sleep(ERROR_RETRY_TIMEOUT)
                self.refresh_connection()

        print("Stopping thread")

    def _handle_dongle_only_state(self, device_name: str) -> None:
        """Handle state when only USB dongle is connected."""
        error_message = "USB dongle is connected, but mouse is not accessible"
        error_menu = Menu(
            MenuItem(device_name, lambda: None, enabled=False),
            MenuItem(error_message, lambda: None, enabled=False),
            MenuItem(f"Please wait; retrying in {ERROR_RETRY_TIMEOUT} seconds", lambda: None, enabled=False),
            MenuItem('Quit', self.quit_app)
        )
        self.update_systray_icon(None, error_message, menu=error_menu)
        time.sleep(POLLING_INTERVAL)
        raise DeviceConnectionError(error_message)

    def _handle_error_state(self, error_message: str) -> None:
        """Handle error state with appropriate UI updates."""
        timestamp = time.strftime('%H:%M:%S')
        print(f"{timestamp} | {error_message}")
        print(f"{timestamp} | Sleeping for {ERROR_RETRY_TIMEOUT} seconds...")

        error_menu = Menu(
            MenuItem(error_message, lambda: None, enabled=False),
            MenuItem(f"Retrying in {ERROR_RETRY_TIMEOUT} seconds...", 
                    lambda: None, enabled=False),
            MenuItem('Quit', self.quit_app)
        )
        self.update_systray_icon(None, error_message, menu=error_menu)

    def update_battery_info(self, battery: DeviceStatus) -> None:
        """Update battery information and refresh UI."""
        self.battery_level = battery['battery']
        self.last_update = time.time()
        self.battery_charging = battery["charging"]

        self.systray_icon.icon = self.create_image(self.battery_level)
        self.systray_icon.menu = self.create_menu(self.device_manager.exists_model['name'])
        self.systray_icon.title = (f"Mouse Battery: "
                                  f"{f'{self.battery_level}%' if self.battery_level is not None else 'N/A'}")

    def update_systray_icon(self, percentage: Optional[int], title: str, menu: Optional[Menu] = None) -> None:
        """Update the system tray icon appearance and menu."""
        self.systray_icon.icon = self.create_image(percentage)
        self.systray_icon.title = title

        if menu is not None:
            self.systray_icon.menu = menu
            self.systray_icon.update_menu()

    def create_image(self, percentage: Optional[int]) -> Image.Image:
        """Create the battery indicator image."""
        img = Image.new('RGBA', ICON_SIZE, color=ICON_BG_COLOR)
        draw = ImageDraw.Draw(img)

        color, level = self.get_color_and_level(percentage)
        draw.rectangle([(0, level), ICON_SIZE], fill=color, outline=None)
        
        font_type = ImageFont.truetype(FONT_NAME, FONT_SIZE)
        draw.text((0, 15), f"{'N/A' if percentage is None else percentage}", 
                 fill=FONT_COLOR, font=font_type)

        return img

    def get_color_and_level(self, percentage: Optional[int]) -> Tuple[str, int]:
        """Get the appropriate color and level for the battery indicator."""
        if percentage is None:
            return BATTERY_LEVELS["unknown"]
        
        if percentage > BATTERY_HIGH:
            return BATTERY_LEVELS["high"]
        elif percentage >= BATTERY_MEDIUM:
            return BATTERY_LEVELS["medium"]
        else:
            return BATTERY_LEVELS["low"]

    def refresh_connection(self, *args) -> None:
        """Refresh the device connection."""
        self.device_manager = DeviceManager()
        self.battery_status = BatteryStatus(self.device_manager)
        self.event.set()

    def quit_app(self, icon: Icon, item: MenuItem) -> None:
        """Clean up and quit the application."""
        self.stopped = True
        icon.stop()

    def start(self) -> None:
        """Initialize and start the system tray application."""
        self.systray_icon = Icon(
            "Battery",
            self.create_image(None),
            "Connecting",
            menu=Menu(
                MenuItem("Loading, please wait...", lambda: None),
                MenuItem('Quit', self.quit_app)
            )
        )

        monitor_thread = threading.Thread(target=self.get_battery)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.systray_icon.run()

def main() -> None:
    """Main entry point of the application."""
    monitor = SystrayIcon()
    monitor.start()

if __name__ == "__main__":
    main()
