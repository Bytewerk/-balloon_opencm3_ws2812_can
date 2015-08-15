__author__ = 'hd'

import time
import random
from socketcan import CanMessage, CanSocket

sock = CanSocket()
sock.open("can0")
msg = CanMessage(0x133701ef, [0,0,255,255])

colors = [0]*10

h = 0
while True:
    h = (h + random.randint(10, 120)) % 360
    colors = colors[1:] + [h]

    for i, h in enumerate(reversed(colors)):
        msg.data[0] = i
        msg.data[1] = int(h/2)
        sock.send(msg)

    time.sleep(1)
