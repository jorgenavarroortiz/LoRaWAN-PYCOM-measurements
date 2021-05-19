import machine
from network import WLAN
import utime
from network import LoRa
import socket
import time
import ubinascii
import crypto
import sys

# Libraries from https://github.com/pycom/pycom-libraries/tree/master/shields/lib
from pycoproc import Pycoproc
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE

boardType = 0

## PARAMETERS
# Period between packets = fixedTime + random (0, fixedTime)
fixedTime = 10.0
randomTime = 10.0

# Debug messages
debug = 0
# OTAA or ABP
# VERY IMPORTANT!!! If ABP is used, make sure that RX2 data rate is set to 5
# and RX2 frequency is set to 869.525 MHz (chirpstack -> device profile ->
# -> join (OTAA/ABP))). Set Class-C confirmed downlink timeout to 5 seconds in
# both cases (chirpstack -> device profile -> class-C)
# IMPORTANT!!!: for ABP, first activate the device (before starting this program)
bOTAA = True
# For OTAA
AppEUI = '1234567890ABCDEF' # Not used
AppKey = '00000000000000000000000000000001'
# For ABP
DevAddr = '00000001'
NwkSKey = '00000000000000000000000000000001'
AppSKey = '00000000000000000000000000000001'
# Retransmission time for JOINREQ
joinReqRtxTime = 5.0

# Measurements
lt_light = None
lt_lux = None
mp_temp = None
mp_alt = None
mp_pres = None
si_temp = None
si_dew = None
si_humid = None
si_humid_tamb = None
li_acc = None
li_roll = None
li_pitch = None

## FUNCTIONS
# General functions
def Random():
  r = crypto.getrandbits(32)
  return ((r[0]<<24)+(r[1]<<16)+(r[2]<<8)+r[3])/4294967295.0

def RandomRange(rfrom, rto):
  return Random()*(rto-rfrom)+rfrom

def zfill(s, width):
  return '{:0>{w}}'.format(s, w=width)

# Functions related to board
def takeMeasurement():
  if boardType == Pycoproc.PYSCAN or boardType == Pycoproc.PYSENSE:
    lt = LTR329ALS01(pyexp)
    lt_light = lt.light()
    lt_lux = lt.lux()
    print("[INFO] LTR329ALS01 light (channel Blue lux, channel Red lux): " + str(lt_light))
    print("[INFO] LTR329ALS01 light (global lux):                        " + str(lt_lux))

  # From https://docs.pycom.io/tutorials/expansionboards/pysense/
  if boardType == Pycoproc.PYSENSE:
    mp = MPL3115A2(pyexp,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
    mp_temp = mp.temperature()
    mp_alt = mp.altitude()
    print("[INFO] MPL3115A2 temperature:                                " + str(mp_temp))
    print("[INFO] MPL3115A2 altitude:                                   " + str(mp_alt))
    mpp = MPL3115A2(pyexp,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters
    mp_pres = mpp.pressure()
    print("[INFO] MPL3115A2 Pressure:                                   " + str(mp_pres))

    si = SI7006A20(pyexp)
    si_temp = si.temperature()
    si_humid = si.humidity()
    si_dew = si.dew_point()
    t_ambient = 24.4
    si_humid_tamb = si.humid_ambient(t_ambient)
    print("[INFO] SI7006A20 temperature:                                " + str(si_temp)+ " deg C")
    print("[INFO] SI7006A20 relative Humidity:                          " + str(si_humid) + " %RH")
    print("[INFO] SI7006A20 dew point:                                  "+ str(si_dew) + " deg C")
    print("[INFO] SI7006A20 humidity ambient for " + str(t_ambient) + " deg C:            " + str(si_humid_tamb) + "%RH")

    li = LIS2HH12(pyexp)
    li_acc = li.acceleration()
    li_roll = li.roll()
    li_pitch = li.pitch()
    print("[INFO] LIS2HH12 acceleration:                                " + str(li_acc))
    print("[INFO] LIS2HH12 roll:                                        " + str(li_roll))
    print("[INFO] LIS2HH12 pitch:                                       " + str(li_pitch))

def detectBoard(lora):
  print("[INFO] Detected board:", sys.platform)

  # Expansion board
  pid = 0
  try:
    pyexp = Pycoproc()
    pid = pyexp.read_product_id()
  except:
    pyexp = None
    print("Detected universal expansion board")
    boardType = Pycoproc.PYUNIV

  if (pid == 61458):   # From web
    print("[INFO] Detected expansion board: PySense (HW version {:d}, FW version {:d})".format(pyexp.read_hw_version(), pyexp.read_fw_version()))
    #pyexp = Pysense()
    boardType = Pycoproc.PYSENSE
  elif (pid == 61459): # From web
    print("[INFO] Detected expansion board: PyTrack (HW version {:d}, FW version {:d})".format(pyexp.read_hw_version(), pyexp.read_fw_version()))
    #pyexp = Pytrack()
    boardType = Pycoproc.PYTRACK
  elif (pid == 61240):   # Testing my own device
    print("[INFO] Detected expansion board: PyScan (HW version {:d}, FW version {:d})".format(pyexp.read_hw_version(), pyexp.read_fw_version()))
    #pyexp = Pycoproc(Pycoproc.PYSCAN)
    boardType = Pycoproc.PYSCAN

  ## WI-FI MAC address
  #print("Device unique ID:", ubinascii.hexlify(machine.unique_id()).upper().decode('utf-8'))
  print("[INFO] Wi-Fi MAC:     ", ubinascii.hexlify(WLAN().mac()[0]).upper().decode('utf-8'))

  ## LORAWAN MAC address
  print("[INFO] LORAWAN DevEUI:", ubinascii.hexlify(lora.mac()).upper().decode('utf-8'))

  return (pyexp, boardType)

# Functions related to LoRaWAN
def initializeLoRaWAN():
  if (bOTAA):
    # Create an OTAA authentication parameters
    app_eui = ubinascii.unhexlify(AppEUI)
    app_key = ubinascii.unhexlify(AppKey)

    # Join a network using OTAA (Over the Air Activation)
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

  else:
    # Create an ABP authentication params
    dev_addr = struct.unpack(">l", ubinascii.unhexlify(DevAddr))[0]
    nwk_swkey = ubinascii.unhexlify(NwkSKey)
    app_swkey = ubinascii.unhexlify(AppSKey)

    # Join a network using ABP (Activation By Personalization)
    lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey), timeout=0)

  # Wait until the module has joined the network
  print('[INFO] Not joined yet...')
  while not lora.has_joined():
    #blink(red, 0.5, 1)
    time.sleep(2.5)
    print('[INFO] Not joined yet...')

  print('[INFO] --- Joined Sucessfully --- ')

  # Create a LoRa socket
  s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
  # Set the LoRaWAN data rate (DR0...DR5 - the lower DR, the higher SF)
  s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
  # Set CONFIRMED to false
  s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False)

  return s

def generateMessage(messageCounter):
  if (messageCounter < 10):
    message = "Testing data....." + str(messageCounter)
  elif (messageCounter < 100):
    message = "Testing data...." + str(messageCounter)
  elif (messageCounter < 1000):
    message = "Testing data..." + str(messageCounter)
  elif (messageCounter < 10000):
    message = "Testing data.." + str(messageCounter)
  else:
    message = "Testing data." + str(messageCounter)

  return message

###################
## MAIN FUNCTION ##
###################

# Real-time clock
rtc = machine.RTC()

# INITIALIZE LORA (LORAWAN mode. Europe = LoRa.EU868)
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, public=True, tx_retries=3, device_class=LoRa.CLASS_C, adr=False)

# BOARD INFORMATION
(pyexp, boardType) = detectBoard(lora)

## LORAWAN (initialize and return a socket)
s = initializeLoRaWAN()

# Infinite loop
messageCounter = 0
while True:

  # Take one measurement
  takeMeasurement()

  # Generate message
  message = generateMessage (messageCounter) # Testing data.....01, ...
  payloadsize = len(message)
  messageCounter = messageCounter + 1

  # Time between transmissions
  randNo = fixedTime + RandomRange(0,randomTime)
  if (debug > 0):
    print("[DEBUG] Time for next transmission = {:.1f}".format(randNo))

  if (messageCounter == 1):
    year, month, day, hour, minute, second, usecond, nothing = rtc.now()
    currentTime = hour*3600 + minute*60 + second + usecond/1000000
    timeNextTransmission = currentTime + randNo
  else:
    # Not the first packet
    timeNextTransmission = timeLastTransmission + randNo

  year, month, day, hour, minute, second, usecond, nothing = rtc.now()
  currentTime = hour*3600 + minute*60 + second + usecond/1000000
  timeToWait = timeNextTransmission - currentTime
  if (debug > 0):
    print("[DEBUG] currentTime = {:.3f}".format(currentTime))
    print("[DEBUG] timeNextTransmission = {:.3f}".format(timeNextTransmission))
    print("[DEBUG] timeToWait = {:.3f}".format(timeToWait))
  timeLastTransmission = timeNextTransmission

  if (timeToWait > 0):
    print("[INFO] Waiting {:.3f} s for next transmission...".format(timeToWait))
    time.sleep(timeToWait)
  else:
    print("[INFO] Next transmission starts immediately (time between transmissions too short)!")

  s.setblocking(True)
  s.send(message)
  s.setblocking(False)

  year, month, day, hour, minute, second, usecond, nothing = rtc.now()
  print("[INFO] Message \"{:s}\" sent at {:02d}:{:02d}:{:02d}.{:.06d}".format(message, hour, minute, second, usecond))
