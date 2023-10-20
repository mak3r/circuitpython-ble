import time
import displayio
import terminalio
import gc
import json

from adafruit_ble import BLERadio
from adafruit_ble import Advertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_clue import clue
from adafruit_display_text import label

# for binding with the matrix portal billboard
BILLBOARD_NAME = "F-nRF52"
# # The background at startup before connection
# STARTUP_BG = "hyvlabs.bmp"

# Display Stuff
display = clue.display
disp_group = displayio.Group()
display.show(disp_group)

# Background BMP pre BLE connection
# hyvbmp = displayio.OnDiskBitmap(open(STARTUP_BG, "rb"))
# image = displayio.TileGrid(hyvbmp, pixel_shader=hyvbmp.pixel_shader)
# disp_group.append(image)

# Billboard content shows up here
in_label = label.Label(terminalio.FONT, text='A'*32, scale=2,
                       color=0xFFFFFF)
in_label.anchor_point = (0, 0)
in_label.anchored_position = (5, 12)
disp_group.append(in_label)

debug_label = label.Label(terminalio.FONT, text='o-o', scale=2, color=0x00FF00)
debug_label.anchor_point = (0,0)
debug_label.anchored_position = (5, 200)
disp_group.append(debug_label)

# This is the bluetooth low energy connection
ble_connection = None
ble = BLERadio()
# print("BLE Radio name:", ble.name)
uart = None
billboard = None
# When we are waiting for a response from sending a prev/next request
await_message = False
# A byte array of json formatted content
response = bytearray('', 'utf-8')


curly_count = 0
def capture_json(data = b''):
    global curly_count
    global await_message
    print(data)
    for i in data:
        if i == b'{'[0]:
            curly_count += 1
        if i == b'}'[0]:
            curly_count -= 1
    if await_message:
        response.extend(data)
        print(response)
    if curly_count == 0:
        await_message = False

# Call this method only after the response variable is believed to have 
# valid json formatted content
def parse_data() -> dict:
    parsed = None
    try:
        parsed = json.loads(response)
    except Exception as e:
        print("failed to parse response:", response)
        #TODO: handle the failure
    return parsed

def update_bg():
    pass

def update_label(content=None):
    if type(content) is dict:
        try:
            in_label.text = content.get("text")
            in_label.color = int(content.get("fg"),16)
            in_label.background_color = int(content.get("bg"),16)
            # ceiling of (clue display dpi / matrix display dpi) [display widths]
            in_label.scale = -(-252//64) 
        except Exception as e:
            c = json.dumps(content)
            err = "Error in dictionary content\n"
            print(err, c)
            update_label(err + c)
    elif type(content) is str:
        in_label.text = content
        in_label.color = 0xFFFFFF
        in_label.background_color = None
        in_label.scale = 2
    else:
        in_label.text = "ERROR\nCONTENT INVALID\nCHECK BILLBOARD"

update_label("[A+B] to scan\nfor billboard")

def clear_connection():
    global uart
    uart = None
    for connection in ble.connections:
        connection.disconnect()

# Scan for advertisements and return the advertisement 
# that matches BILLBOARD_NAME
def scan() -> Advertisement :
    # A completed scan could be from a successful connection
    # or from a scan timeout
    print("Free memory: %s"%str(gc.mem_free()))
    print("Allocated memory: %s"%str(gc.mem_alloc()))
    # this will be assigned to the Advertisement for the billboard we want to connect with
    ad = None
    try:
        # Keeping buffer size low seems to reduce the memory amount attempting to be allocated
        #   Default is 512
        for advert in ble.start_scan(buffer_size=128,timeout=2):
            print(f"{advert=}")
            if advert.complete_name == BILLBOARD_NAME:
                ad = advert
                update_label("Found {} \n{}".format(ad.complete_name, "[A+B] to connect"))
                break
    except Exception as e:
        print(e)

    ble.stop_scan()
    gc.collect()
    return ad


def connect(billboard=None):
    global uart
    if billboard:
        try:
            ble.connect(billboard)
            billboard = None
            for connection in ble.connections:
                if not connection.connected:
                    continue
                # print("Check connections for uart service")
                if UARTService not in connection:
                    continue
                # print("Connection has uart service")
                uart = connection[UARTService]
                update_label("\0")
                # print("Connected to peripheral via uart.")
                break
        except Exception as e:
            if billboard:
                update_label("Unable to connect \nto {}.\nPlease rescan[A+B].".format(billboard.complete_name))
            else:
                update_label("Connection failed.\nTry rescan[A+B].")
            print(e)

response_delay = 50 #milliseconds
def write_ble(content:bytes = b''):
    global await_message
    global response
    response_time = time.monotonic()
    uart.reset_input_buffer()
    uart.write(content)
    await_message = True
    while uart.in_waiting is 0:
        #block until a response is received or the response delay
        # time expires
        if time.monotonic() - response_time > response_delay:
            print("response delay expired")
            break;
    
    data = b''
    response = bytearray('', 'utf-8')
    while await_message:
        byte_count = uart.in_waiting
        data = uart.read(byte_count)
        if data:
            capture_json(data) #tests for await_message is True

    msg = parse_data()
    print(msg)
    print(json.dumps(msg)) # a string object
    
    update_label(msg)

#NOTE: Consider using Packets for transporting billboard data
button_delay = 0.2
last_time = time.monotonic()
while True:
    if ble.connected:
        if (time.monotonic() - last_time) > button_delay:
            if uart:
                if clue.button_b:
                    debug_label.text = 'B'
                    clue.start_tone(587)
                    write_ble(b'n')

                if clue.button_a:
                    debug_label.text = 'A'
                    clue.start_tone(523)
                    write_ble(b'p')

            if clue.button_a and clue.button_b:
                clue.start_tone(459)
                clear_connection()

            last_time = time.monotonic()
        


    else: #BLE not connected
        if clue.button_a and clue.button_b:
            if not billboard:
                billboard = scan()
            else:
                connect(billboard=billboard)
    
    clue.stop_tone()


