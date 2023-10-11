# Echo server for BLE 
# This device is the peripheral

import board
from adafruit_ble import BLERadio
from adafruit_ble.services.nordic import UARTService
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement

ble = BLERadio()
print("BLE Radio name:", ble.name)
ble_connection = None # BLEConnection object
uart = UARTService()
advert = ProvideServicesAdvertisement(uart)

advert.complete_name = "F-nRF52"
STALE_CONNECTION = False #when the peer disconnects we have a stale connection 

def advertise():
	global advert
	if not ble.advertising:
		print("Start Advertising")
		ble.start_advertising(advert)

def stop_advertising():
	if ble.advertising:
		print("Stop Advertising")
		ble.stop_advertising()

def reset_stale_connection():
	for connection in ble.connections:
		connection.disconnect()
		connection = None

def reset_advertising():
	stop_advertising()
	advertise()

if not ble.connected:
	stop_advertising()

print("Entering main loop")

uart.reset_input_buffer()
while True:	
	if ble.connected:
		if ble_connection:
			STALE_CONNECTION = True # if we lose the connection now, it is considered stale
			if uart: # and uart.in_waiting > 0:
				data = uart.read(uart.in_waiting)
				if data:
					uart.write(data)
					uart.reset_input_buffer()
					print(data)
		else:
			print("no BLEConnection")
			# Try to acquire a BLEConnection
			for connection in ble.connections:
				if connection.connected:
					ble_connection = connection
					stop_advertising()
			# # # Now let's advertise for a new connection
			# # advertise()
			
	else: #BLERadio is not connected
		try:
			if STALE_CONNECTION:
				print(f"{STALE_CONNECTION=}")
				reset_stale_connection()
				reset_advertising()
				STALE_CONNECTION = False
			else:
				# if ble_connection and ble_connection.connected:
				# 	ble_connection.disconnect()
				# ble_connection = None
				#stop_advertising()
				advertise()
				# print("ble not connected")
				# print("*** advertising ******: ", ble.advertising)
		except Exception as e:
			print(e)