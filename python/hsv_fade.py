__author__ = 'hd'

import time
from socketcan import CanMessage, CanSocket

sock = CanSocket()
sock.open("can0")
msg = CanMessage(0x133701ef, [0,0,255,255])
h = 0

while True:

    msg.data[0] = 0
    msg.data[1] = h % 180
    sock.send(msg)

    msg.data[0] = 1
    msg.data[1] = (h + 20) % 180
    sock.send(msg)

    msg.data[0] = 2
    msg.data[1] = (h + 40) % 180
    sock.send(msg)

    h += 1
    time.sleep(0.05)
