# Pycom node sending measurements using LoRaWAN

© Jorge Navarro-Ortiz (jorgenavarro@ugr.es), University of Granada

This code has been tested with FiPy nodes with PySense, PyTrack, PyScan and the universal expansion board.
In the case of PySense, it sends lux (LTR329ALS01), temperature (SI7006A20), humidity (SI7006A20) and pressure (MPL3115A2) values. In the case of PyTrack, only lux (LTR329ALS01) values are sent. For the other expansion boards, a test message is sent. For simplicity, these values are sent as strings with two decimals.

Sensor libraries are taken from Pycom repository: https://github.com/pycom/pycom-libraries/tree/master/shields/lib

Before uploading the code to a Pycom node, please remember to remove the ``img`` directory (which contains images for this README, but should not be uploaded to the node).

**Example of messages shown through the serial port (FiPy with a PySense expansion board)**

![pycom-lorawan-measurements-console](https://user-images.githubusercontent.com/17797704/145732311-48e051e7-2728-4f46-a4a1-c0bff8249841.png)
