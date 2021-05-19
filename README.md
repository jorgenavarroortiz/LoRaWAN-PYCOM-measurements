# Pycom node sending measurements using LoRaWAN

© Jorge Navarro-Ortiz (jorgenavarro@ugr.es), University of Granada

This code has been tested with FiPy nodes with PySense, PyTrack, PyScan and the universal expansion board.
In the case of PySense, it sends lux (LTR329ALS01), temperature (SI7006A20), humidity (SI7006A20) and pressure (MPL3115A2) values. In the case of PyTrack, only lux (LTR329ALS01) values are sent. For the other expansion boards, a test message is sent.

Sensor libraries are taken from Pycom repository: https://github.com/pycom/pycom-libraries/tree/master/shields/lib
