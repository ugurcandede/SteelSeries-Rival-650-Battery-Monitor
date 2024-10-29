#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time

from PIL import Image, ImageDraw, ImageFont
from pystray import Icon, MenuItem, Menu

from _init import DeviceManager, BatteryStatus

REFRESH_TIMEOUT = 60
ERROR_RETRY_TIMEOUT = 10


class SystrayIcon:
    def __init__(self):
        self.device_manager = DeviceManager()
        self.battery_status = BatteryStatus(self.device_manager)
        self.last_update = None
        self.battery_level = None
        self.battery_charging = None
        self.systray_icon = None
        self.stopped = False
        self.event = threading.Event()

    def create_menu(self, name):
        return Menu(
            MenuItem(f"Name: {name}", lambda: None, enabled=False),
            MenuItem(f"Battery: {str(f'{self.battery_level}%' if self.battery_level is not None else 'N/A')}", lambda: None, enabled=False),
            MenuItem(f"Status: {'Charging' if self.battery_charging else 'Discharging'}", lambda: None, enabled=False),
            MenuItem("Last update: " + time.strftime("%H:%M:%S", time.localtime(self.last_update)) + " (click to refresh)", self.refresh_connection),
            MenuItem("Quit", self.quit_app),
        )

    def get_battery(self):
        while not self.stopped:
            try:
                device = self.device_manager.exists_model
                device_name = device['name']

                print(f"{time.strftime('%H:%M:%S')} | Mouse found: {device_name}")
                battery = self.battery_status.get_status()

                if battery['name'] == "No device found":
                    self.update_systray_icon(None, "USB dongle is connected, but no mouse found", menu=Menu(
                        MenuItem(device_name, lambda: None, enabled=False),
                        MenuItem("USB dongle is connected, but no mouse found", lambda: None, enabled=False),
                        MenuItem(f"Please wait; retrying in {REFRESH_TIMEOUT} seconds", lambda: None, enabled=False),
                        MenuItem('Quit', self.quit_app)
                    ))
                    time.sleep(1 / 20)
                    raise Exception("USB dongle is connected, but no mouse found")

                self.update_battery_info(battery)

                sleep_time = REFRESH_TIMEOUT if self.battery_level is not None else 1 / 20
                self.event.clear()
                self.event.wait(timeout=sleep_time)

            except Exception as e:
                print(f"Error: {e}\n\n{time.strftime('%H:%M:%S')} | Sleeping for {REFRESH_TIMEOUT} seconds...")
                time.sleep(ERROR_RETRY_TIMEOUT)
                self.event.set()

        print("Stopping thread")

    def update_battery_info(self, battery):
        self.battery_level = battery['battery']
        self.last_update = time.time()
        self.battery_charging = battery["charging"]

        self.systray_icon.icon = self.create_image(self.battery_level)
        self.systray_icon.menu = self.create_menu(self.device_manager.exists_model['name'])
        self.systray_icon.title = f"Mouse Battery: {str(f'{self.battery_level}%' if self.battery_level is not None else 'N/A')}"

    def update_systray_icon(self, percentage, title, menu):
        self.systray_icon.icon = self.create_image(percentage)
        self.systray_icon.title = title

        if menu is not None:
            self.systray_icon.menu = menu

        self.systray_icon.update_menu()

    def create_image(self, percentage):
        img = Image.new('RGBA', (50, 50), color=(255, 255, 255, 90))
        d = ImageDraw.Draw(img)

        color, level = self.get_color_and_level(percentage)

        d.rectangle([(0, level), (50, 50)], fill=color, outline=None)
        font_type = ImageFont.truetype("arial.ttf", 31)
        d.text((0, 15), f"{'N/A' if percentage is None else percentage}", fill="white", font=font_type)

        return img

    def get_color_and_level(self, percentage):
        if percentage is None:
            return "purple", 0

        if percentage <= 20:
            return "red", 40
        elif percentage <= 50:
            return "orange", 25
        else:
            return "green", 0

    def refresh_connection(self):
        self.event.set()

    def quit_app(self, icon, item):
        self.stopped = True
        icon.stop()

    def start(self):
        self.systray_icon = Icon("Battery", self.create_image(None), "Connecting", menu=Menu(
            MenuItem("Loading, please wait...", lambda: None),
            MenuItem('Quit', self.quit_app)
        ))

        thread = threading.Thread(target=self.get_battery)
        thread.daemon = True
        thread.start()

        self.systray_icon.run()


def main():
    monitor = SystrayIcon()
    monitor.start()


if __name__ == "__main__":
    main()
