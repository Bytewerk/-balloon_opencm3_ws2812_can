__author__ = 'hd'

import struct


class CanMessage:
    # CAN frame packing/unpacking (see `struct can_frame` in <linux/can.h>)
    frame_fmt = "=IB3x8s"

    def __init__(self, id, data=[], is_extended=False, is_rtr=False):
        self.id = id & 0x1FFFFFFF
        self.is_extended = is_extended or ((id & 0x80000000) != 0)
        self.is_rtr = is_rtr or ((id & 0x40000000) != 0)
        self.data = data

    def __str__(self):
        if self.is_extended or self.id>0x7FF:
            id_str = "0x%08x" % self.id
        else:
            id_str = "     0x%03x" % self.id
        data_str = " ".join(("%02x" % (i,)) for i in self.data)
        return "%s %s" % (id_str, data_str)

    def set_signal(self, start_bit, signal_length, value, big_endian=False):
        message_data = 0
        if big_endian:
            for b in self.data:
                message_data = (message_data << 8) | b
        else:
            for b in reversed(self.data):
                message_data = (message_data << 8) | b
            start_bit = 64 - start_bit - signal_length

        signal_mask = (2**signal_length - 1) << (64-signal_length-start_bit)

        message_data &= ~signal_mask
        message_data |= (value << (64-signal_length-start_bit)) & signal_mask

        if big_endian:
            for i in range(len(self.data)-1, -1, -1):
                self.data[i] = message_data & 0xFF
                message_data >>= 8
        else:
            for i in range(0, len(self.data)):
                self.data[i] = message_data & 0xFF
                message_data >>= 8

    def get_signal(self, start_bit, signal_length, big_endian=False):
        result = 0
        if big_endian:
            for b in self.data:
                result = (result << 8) | b
        else:
            for b in reversed(self.data):
                result = (result << 8) | b

        result >>= (64-start_bit-signal_length)
        result &= 2**signal_length - 1
        return result

    def from_raw(frame):
        id, dlc, data = struct.unpack(CanMessage.frame_fmt, frame)
        data_arr = []
        for x in data[:dlc]:
            data_arr.append(x)
        return CanMessage(id, data_arr)

    def to_raw(self):
        id = self.id
        if (id>0x7FF) or self.is_extended:
            id |= 0x80000000
        if self.is_rtr:
            id |= 0x40000000
        dlc = len(self.data)
        bdata = bytearray()
        for x in self.data:
            bdata.append(x)
        return struct.pack(CanMessage.frame_fmt, id, dlc, bdata.ljust(8, b'\x00'))
