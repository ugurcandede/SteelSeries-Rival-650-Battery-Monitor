HID_REPORT_TYPE_OUTPUT = 0x02

profile = [
    {
        "name": "SteelSeries Rival 650 Wireless",
        "models": [
            {
                "name": "SteelSeries Rival 650 (wired mode)",
                "vendor_id": 0x1038,
                "product_id": 0x172B,
                "endpoint": 0,
            },
            {
                "name": "SteelSeries Rival 650 (wireless mode)",
                "vendor_id": 0x1038,
                "product_id": 0x1726,
                "endpoint": 0,
            },
        ],
        "battery_level": {
            "report_type": HID_REPORT_TYPE_OUTPUT,
            "command": [0xAA, 0x01],
            "response_length": 3,
            "is_charging": lambda data: bool(data[2]),
            "level": lambda data: int(data[0]),
        }
    }
]
