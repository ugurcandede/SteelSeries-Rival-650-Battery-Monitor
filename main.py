#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Author: Ugurcan Dede
Date: 2024-10-28
GitHub: https://github.com/ugurcandede

Description:
This script prints the battery level of the SteelSeries Rival 650 Wireless mouse to the console.
It utilizes the 'hid' library to communicate with the device and retrieves battery information through HID reports.
The program opens a connection to the mouse, sends a command to request the battery level, and processes the response
to determine the battery percentage and charging status.

Usage:
Run this script to check the battery status of the connected SteelSeries Rival 650 Wireless mouse. The output will
display the battery percentage and whether the device is currently charging.
"""

import hid
import rival650


def _load_models():
    return [
        {
            "name": model["name"],
            "vendor_id": model["vendor_id"],
            "product_id": model["product_id"],
            "endpoint": model["endpoint"]
        }
        for model in rival650.profile["models"]
    ]


class DeviceManager:
    def __init__(self):
        self.models = _load_models()
        self.exists_model = self.find_exits_model()

    def open_device(self, vendor_id, product_id, endpoint=0):
        hid_device = hid.device()
        for interface in hid.enumerate(vendor_id, product_id):
            if interface["interface_number"] == endpoint and interface["usage"] == 1:
                hid_device.open_path(interface["path"])
                return HIDDevice(hid_device, vendor_id, product_id, endpoint)
        raise Exception("No device found")

    def find_exits_model(self):
        for model in self.models:
                for interface in hid.enumerate(model['vendor_id'], model['product_id']):
                    if interface["interface_number"] == model['endpoint'] and interface["usage"] == 1:
                        return model

class HIDDevice:
    def __init__(self, device, vendor_id, product_id, endpoint):
        self.device = device
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.endpoint = endpoint

    def hid_write(self, report_type=rival650.HID_REPORT_TYPE_OUTPUT, report_id=0x00, data=[], packet_length=0):
        if packet_length > 0:
            bytes_ = bytearray([report_id] + data + [0x00] * (packet_length - 1 - len(data)))
        else:
            bytes_ = bytearray([report_id] + data)

        if report_type == rival650.HID_REPORT_TYPE_OUTPUT:
            self.device.write(bytes_)
        else:
            raise ValueError(f"Invalid HID report type: {report_type:02x}")

    def read(self, response_length, timeout_ms=200):
        return self.device.read(response_length, timeout_ms)

    def close(self):
        self.device.close()


class BatteryStatus:
    def __init__(self, device_manager):
        self.device_manager = device_manager

    def get_status(self):
        status = {}
        for model in self.device_manager.models:
            hid_device = None
            try:
                hid_device = self.device_manager.open_device(model['vendor_id'], model['product_id'], model['endpoint'])
                hid_device.hid_write(
                    report_type=rival650.profile["battery_level"]["report_type"],
                    data=rival650.profile["battery_level"]["command"]
                )
                data = hid_device.read(rival650.profile["battery_level"]["response_length"])

                status.update({
                    "name": model['name'],
                    "battery": rival650.profile["battery_level"]["level"](data),
                    "charging": rival650.profile["battery_level"]["is_charging"](data)
                })

            except Exception:
                pass
            finally:
                if hid_device is not None:
                    hid_device.close()
        if len(status) == 0:
            status.update({"name": "No device found", "battery": None, "charging": None})
        return status


if __name__ == '__main__':
    device_manager = DeviceManager()
    battery_status = BatteryStatus(device_manager)

    device = battery_status.get_status()
    print(f"{device['name']} | %{device['battery']} and it is {'(charging)' if device['charging'] else 'not charging'}")
