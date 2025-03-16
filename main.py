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
from typing import Optional, Tuple, List

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
    "high": ("#4CAF50", 5),     # Material Design Green
    "medium": ("#FF9800", 15),  # Material Design Orange
    "low": ("#F44336", 30),     # Material Design Red
    "unknown": ("#9C27B0", 5)   # Material Design Purple
}

# Text Colors for Different Backgrounds
TEXT_COLORS = {
    "#4CAF50": "#FFFFFF",  # White on Green
    "#FF9800": "#000000",  # Black on Orange
    "#F44336": "#FFFFFF",  # White on Red
    "#9C27B0": "#FFFFFF",  # White on Purple
}

# Charging Indicator Settings
CHARGING_INDICATOR = {
    "color": "#FFD700",        # Gold color for charging
    "glow_color": "#FFE57F",   # Light yellow for glow effect
    "size": 12,                # Size of the indicator
    "border": 2,               # Border thickness
    "position": (4, 4),        # Top-left position
    "symbol_color": "#2C2C2C"  # Dark gray for the lightning symbol
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

        title_parts = [
            "Mouse Battery:",
            f"{self.battery_level}%" if self.battery_level is not None else "N/A",
        ]
        
        if self.battery_charging:
            title_parts.append("(Charging ⚡)")

        self.systray_icon.icon = self.create_image(self.battery_level)
        self.systray_icon.menu = self.create_menu(self.device_manager.exists_model['name'])
        self.systray_icon.title = " ".join(title_parts)

    def update_systray_icon(self, percentage: Optional[int], title: str, menu: Optional[Menu] = None) -> None:
        """Update the system tray icon appearance and menu."""
        self.systray_icon.icon = self.create_image(percentage)
        self.systray_icon.title = title

        if menu is not None:
            self.systray_icon.menu = menu
            self.systray_icon.update_menu()

    def create_image(self, percentage: Optional[int]) -> Image.Image:
        """Create the battery indicator image with modern design."""
        # Create base image with transparency
        img = Image.new('RGBA', ICON_SIZE, color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Get battery color and level
        color, level = self.get_color_and_level(percentage)
        
        # Calculate actual drawing coordinates
        start_y = max(0, min(level, ICON_SIZE[1] - 8))  # Ensure y coordinate is within bounds
        
        # Draw rounded rectangle for battery background
        radius = 8
        self._draw_rounded_rectangle(
            draw,
            [(0, start_y), ICON_SIZE],
            color,
            radius
        )

        # Draw percentage text with better positioning
        font_type = ImageFont.truetype(FONT_NAME, FONT_SIZE)
        text = 'N/A' if percentage is None else str(percentage)
        
        # Calculate text position for center alignment
        text_bbox = draw.textbbox((0, 0), text, font=font_type)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (ICON_SIZE[0] - text_width) // 2
        
        # Get appropriate text color for current background
        text_color = TEXT_COLORS.get(color, "#FFFFFF")
        
        # Draw main text
        draw.text(
            (text_x, 15),
            text,
            fill=text_color,
            font=font_type
        )

        # Draw charging indicator if charging
        if self.battery_charging:
            self._draw_charging_indicator(draw)

        return img

    def _draw_rounded_rectangle(self, draw: ImageDraw.Draw,
                              coords: List[Tuple[int, int]],
                              color: str,
                              radius: int) -> None:
        """Draw a rounded rectangle."""
        x1, y1 = coords[0]
        x2, y2 = coords[1]

        # Draw main rectangle
        draw.rectangle(
            [(x1 + radius, y1), (x2 - radius, y2)],
            fill=color
        )
        draw.rectangle(
            [(x1, y1 + radius), (x2, y2 - radius)],
            fill=color
        )

        # Draw corners
        draw.pieslice([(x1, y1), (x1 + radius * 2, y1 + radius * 2)],
                     180, 270, fill=color)
        draw.pieslice([(x2 - radius * 2, y1), (x2, y1 + radius * 2)],
                     270, 360, fill=color)
        draw.pieslice([(x1, y2 - radius * 2), (x1 + radius * 2, y2)],
                     90, 180, fill=color)
        draw.pieslice([(x2 - radius * 2, y2 - radius * 2), (x2, y2)],
                     0, 90, fill=color)

    def _draw_charging_indicator(self, draw: ImageDraw.Draw) -> None:
        """Draw an animated-looking charging indicator."""
        ci = CHARGING_INDICATOR
        x, y = ci["position"]
        size = ci["size"]
        
        # Draw outer glow
        glow_size = size + 4
        draw.ellipse(
            [(x - 2, y - 2), (x + glow_size, y + glow_size)],
            fill=ci["glow_color"]
        )
        
        # Draw main circle
        draw.ellipse(
            [(x, y), (x + size, y + size)],
            fill=ci["color"],
            outline=ci["glow_color"],
            width=ci["border"]
        )

        # Draw lightning bolt symbol
        bolt_points = [
            (x + size//2 - 2, y + 2),           # Top point
            (x + size//2 + 3, y + size//2),     # Middle right
            (x + size//2 - 1, y + size//2),     # Middle center
            (x + size//2 + 2, y + size - 2)     # Bottom point
        ]
        draw.line(bolt_points, fill=ci["symbol_color"], width=2)

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
