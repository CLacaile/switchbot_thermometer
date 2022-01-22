#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Based on sbm2mqtt.py https://github.com/ronschaeffer/sbm2mqtt
# but writes the sensor data to a file instead of a MQTT Broker

from bluepy.btle import Scanner, DefaultDelegate, ScanEntry
import datetime
import json

# Import config
from config import (
    sensor_data_file_path,
    temperature_file_path,
    humidity_file_path,
    battery_file_path
)

# SwitchBot UUID - See https://github.com/OpenWonderLabs/python-host/wiki/Meter-BLE-open-API
service_uuid = "cba20d00-224d-11e6-9fb8-0002a5d5c51b"


class ScanDelegate(DefaultDelegate):
    # Scan for BLE device advertisements, filter out ones which are not SwitchBot Meters & convert the service data to binary
    def handleDiscovery(self, dev, isNewDev, isNewData):
        services = dev.getValue(ScanEntry.COMPLETE_128B_SERVICES)
        service_data = dev.getValue(ScanEntry.SERVICE_DATA_16B)

        # Check for model "T" (54) in 16b service data
        if (
            services and services[0] == service_uuid
            and service_data and len(service_data) == 8 and service_data[2] == 0x54
        ):
            mac = dev.addr
            binvalue = service_data

            # Get temperature and related characteristics
            temperature = (binvalue[6] & 0b01111111) + (
                (binvalue[5] & 0b00001111) / 10
            )  # Absolute value of temp
            if not (binvalue[6] & 0b10000000):  # Is temp negative?
                temperature = -temperature
            if not (binvalue[7] & 0b10000000):  # C or F?
                temp_scale = "C"
            else:
                temp_scale = "F"
                temperature = round(
                    temperature * 1.8 + 32, 1
                )  # Convert to F

            # Get other info
            humidity = binvalue[7] & 0b01111111
            battery = binvalue[4] & 0b01111111

            # Get current time
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Construct temperature JSON
            temperature_data = json.dumps({
                "address": mac,
                "time": time,
                "temperature": temperature,
                "temperature_scale": temp_scale,
                "signal_strength": dev.rssi,
            })

            # Print temperature into data file
            with open(temperature_file_path, "w+") as f:
                f.write(temperature_data)
                f.close()

            # Print temperature to the console
            print(temperature_data)

            # Construct humidity JSON
            humidity_data = json.dumps({
                "address": mac,
                "time": time,
                "humidity": humidity,
                "signal_strength": dev.rssi,
            })

            # Print humidity into data file
            with open(humidity_file_path, "w+") as f:
                f.write(humidity_data)
                f.close()

            # Print to the console
            print(humidity_data)

            # Construct battery JSON
            battery_data = json.dumps({
                "address": mac,
                "time": time,
                "battery": battery,
                "signal_strength": dev.rssi,
            })

            # Print battery into data file
            with open(battery_file_path, "w+") as f:
                f.write(battery_data)
                f.close()

            # Print to the console
            print(battery_data)


def main():

    print("\nScanning for SwitchBot Meters...")
    scan = scanner = Scanner().withDelegate(ScanDelegate())
    scanner.scan(10.0)

    print("\nFinished.\n")


if __name__ == "__main__":
    main()
