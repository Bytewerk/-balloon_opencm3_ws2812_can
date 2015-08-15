__author__ = 'hd'

import socket
from socketcan import CanMessage

class CanSocket:

    def __init__(self):
        self.sock = None

    def open(self, interface):
        self.sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        #self.sock.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_LOOPBACK, 0)
        #self.sock.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_RECV_OWN_MSGS, 0)
        self.sock.bind((interface,))

    def close(self):
        self.sock.close()

    def read(self, timeout=None):
        self.sock.settimeout(timeout)
        try:
            frame, addr = self.sock.recvfrom(16)
            msg = CanMessage.from_raw(frame)
            print("recv: ", msg)
            return msg
        except socket.timeout:
            return None

    def send(self, msg):
        print("send: ", msg)
        frame = msg.to_raw()
        self.sock.send(frame)
