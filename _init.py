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

from typing import List, Optional, TypedDict

import hid

import devices

# Constants
HID_USAGE_VALUE = 1
DEFAULT_TIMEOUT_MS = 200
DEFAULT_REPORT_ID = 0x00

class DeviceModel(TypedDict):
    name: str
    vendor_id: int
    product_id: int
    endpoint: int

class DeviceStatus(TypedDict):
    name: str
    battery: Optional[int]
    charging: Optional[bool]

class DeviceNotFoundError(Exception):
    """Raised when no compatible device is found."""
    pass

class InvalidHIDReportError(Exception):
    """Raised when an invalid HID report type is provided."""
    pass

def _load_models() -> List[DeviceModel]:
    """Load and return a list of supported device models from the devices profile."""
    return [
        {
            "name": model["name"],
            "vendor_id": model["vendor_id"],
            "product_id": model["product_id"],
            "endpoint": model["endpoint"]
        }
        for models in devices.profile 
        for model in models["models"]
    ]

class DeviceManager:
    def __init__(self):
        self.models = _load_models()
        self.exists_model = self.find_existing_model()

    def verify_device_access(self, vendor_id: int, product_id: int, endpoint: int = 0) -> bool:
        """
        Verify if the device can be actually accessed, not just enumerated.
        
        Args:
            vendor_id: The vendor ID of the device
            product_id: The product ID of the device
            endpoint: The endpoint number
            
        Returns:
            bool: True if device can be accessed, False otherwise
        """
        try:
            hid_device = hid.device()
            for interface in hid.enumerate(vendor_id, product_id):
                if interface["interface_number"] == endpoint and interface["usage"] == HID_USAGE_VALUE:
                    hid_device.open_path(interface["path"])
                    hid_device.close()
                    return True
            return False
        except Exception:
            return False

    def open_device(self, vendor_id: int, product_id: int, endpoint: int = 0) -> 'HIDDevice':
        """
        Open a connection to a HID device with the specified parameters.
        
        Args:
            vendor_id: The vendor ID of the device
            product_id: The product ID of the device
            endpoint: The endpoint number (default: 0)
            
        Returns:
            HIDDevice: An instance of the HIDDevice class
            
        Raises:
            DeviceNotFoundError: If no device matching the criteria is found
        """
        if not self.verify_device_access(vendor_id, product_id, endpoint):
            raise DeviceNotFoundError(f"Device found but cannot be accessed - VID: {vendor_id:04x}, PID: {product_id:04x}")

        hid_device = hid.device()
        for interface in hid.enumerate(vendor_id, product_id):
            if interface["interface_number"] == endpoint and interface["usage"] == HID_USAGE_VALUE:
                try:
                    hid_device.open_path(interface["path"])
                    return HIDDevice(hid_device, vendor_id, product_id, endpoint)
                except Exception as e:
                    raise DeviceNotFoundError(f"Failed to open device - VID: {vendor_id:04x}, PID: {product_id:04x}: {str(e)}")
                
        raise DeviceNotFoundError(f"No device found with VID: {vendor_id:04x}, PID: {product_id:04x}")

    def find_existing_model(self) -> Optional[DeviceModel]:
        """Find and return the first connected device model from the supported models list."""
        for model in self.models:
            if self.verify_device_access(model['vendor_id'], model['product_id'], model['endpoint']):
                return model
        return None

class HIDDevice:
    def __init__(self, device: hid.device, vendor_id: int, product_id: int, endpoint: int):
        self.device = device
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.endpoint = endpoint

    def hid_write(self, report_type: int = devices.HID_REPORT_TYPE_OUTPUT, 
                 report_id: int = DEFAULT_REPORT_ID, 
                 data: List[int] = None, 
                 packet_length: int = 0) -> None:
        """
        Write data to the HID device.
        
        Args:
            report_type: The type of HID report
            report_id: The report ID
            data: The data to write
            packet_length: The length of the packet
            
        Raises:
            InvalidHIDReportError: If an invalid report type is provided
        """
        data = data or []
        if packet_length > 0:
            bytes_ = bytearray([report_id] + data + [0x00] * (packet_length - 1 - len(data)))
        else:
            bytes_ = bytearray([report_id] + data)

        if report_type == devices.HID_REPORT_TYPE_OUTPUT:
            self.device.write(bytes_)
        else:
            raise InvalidHIDReportError(f"Invalid HID report type: {report_type:02x}")

    def read(self, response_length: int, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> List[int]:
        """Read data from the HID device."""
        return self.device.read(response_length, timeout_ms)

    def close(self) -> None:
        """Close the connection to the HID device."""
        self.device.close()

class BatteryStatus:
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager

    def get_status(self) -> DeviceStatus:
        """
        Get the battery status of the connected device.
        
        Returns:
            DeviceStatus: A dictionary containing the device name, battery level, and charging status
        """
        status: DeviceStatus = {"name": "No device found", "battery": None, "charging": None}
        
        if not self.device_manager.exists_model:
            return status

        # First try the model that was detected as accessible
        existing_model = self.device_manager.exists_model
        device_profile = next(
            (device_ for device_ in devices.profile 
             if any(model_["product_id"] == existing_model["product_id"] 
                   for model_ in device_["models"])),
            None
        )

        if device_profile:
            battery_profile = device_profile["battery_level"]
            hid_device = None
            try:
                hid_device = self.device_manager.open_device(
                    existing_model['vendor_id'], 
                    existing_model['product_id'], 
                    existing_model['endpoint']
                )

                hid_device.hid_write(
                    report_type=battery_profile["report_type"],
                    data=battery_profile["command"]
                )

                data = hid_device.read(battery_profile["response_length"])
                
                # Check if we received valid data
                if data and len(data) >= battery_profile["response_length"]:
                    status.update({
                        "name": existing_model['name'],
                        "battery": battery_profile["level"](data),
                        "charging": battery_profile["is_charging"](data)
                    })
                    return status
                else:
                    print(f"Warning: Received incomplete data from device: {data}")

            except (DeviceNotFoundError, InvalidHIDReportError, IndexError) as e:
                print(f"Warning: Could not read from detected device: {str(e)}")
            finally:
                if hid_device is not None:
                    hid_device.close()

        # If the detected model failed, try other models in the same profile silently
        profile_groups = {}
        for model in self.device_manager.models:
            # Skip the model we already tried
            if model["product_id"] == existing_model["product_id"]:
                continue
                
            device_profile = next(
                (device_ for device_ in devices.profile 
                 if any(model_["product_id"] == model["product_id"] 
                       for model_ in device_["models"])),
                None
            )
            if device_profile:
                profile_name = device_profile["name"]
                if profile_name not in profile_groups:
                    profile_groups[profile_name] = []
                profile_groups[profile_name].append(model)

        # Try each profile group
        for profile_name, models in profile_groups.items():
            device_profile = next(
                device_ for device_ in devices.profile 
                if device_["name"] == profile_name
            )
            battery_profile = device_profile["battery_level"]

            # Try each model in the profile
            for model in models:
                hid_device = None
                try:
                    hid_device = self.device_manager.open_device(
                        model['vendor_id'], 
                        model['product_id'], 
                        model['endpoint']
                    )

                    hid_device.hid_write(
                        report_type=battery_profile["report_type"],
                        data=battery_profile["command"]
                    )

                    data = hid_device.read(battery_profile["response_length"])
                    
                    # Check if we received valid data
                    if not data or len(data) < battery_profile["response_length"]:
                        continue

                    status.update({
                        "name": model['name'],
                        "battery": battery_profile["level"](data),
                        "charging": battery_profile["is_charging"](data)
                    })
                    return status

                except (DeviceNotFoundError, InvalidHIDReportError, IndexError):
                    continue
                finally:
                    if hid_device is not None:
                        hid_device.close()

        return status

def main() -> None:
    """Main function to get and display the battery status."""
    device_manager = DeviceManager()
    battery_status = BatteryStatus(device_manager)

    device = battery_status.get_status()
    print(f"{device['name']} | %{device['battery']} and it is {'charging' if device['charging'] else 'not charging'}")

if __name__ == '__main__':
    main()
