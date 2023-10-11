# circuitpython-ble
Implentation of BLE Uart communication using circuitpython

## Target boards
This has been tested only with boards sporting the nRF52840. There may be other boards that can use circuit python and ble that are untested.
Adafruit Clue
Adafruit Feather Express

## Usage
* Install central role on the clue
* Install peripheral role on the feather
* Clue sends messages
* Feather receives messages and echos them back
* Clue receives messages returned from peripheral