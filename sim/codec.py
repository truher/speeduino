#!/usr/bin/env python
#
# encoding only, no domain
#
# use arduino crc16.h and python crcmod
#
# TODO: use COBS

# message format is
#
# struct packet {
#   struct payload {
#     field x;
#     field y;
#     ...
#   }
#   uint16 crc
# }

import crcmod
import struct
from cobs import cobs

#class Payload:

#class Packet:

class Codec:
    crcStruct = struct.Struct("<H")
    def __init__(self):
        self.xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')

    def crc(self, data):
        return self.xmodem_crc_func(data)

    def packCrc(self, data):
        return Codec.crcStruct.pack(data)

    def unPackCrc(self, data):
        if len(data) != 2:
            raise ValueError("bad CRC len %d" % len(data))
        return Codec.crcStruct.unpack(data)[0]

    def crcBytes(self, data):
        return self.packCrc(self.crc(data))

    def crcCheck(self, data, crc):
        return (self.crc(data) == crc)

    def extractCrc(self, packetBytes):
        if len(packetBytes) <= 2:
            raise ValueError("bad packet len %d" % len(packetBytes))
        crcBytes = packetBytes[- 2 : ]
        return self.unPackCrc(crcBytes)

    def packetEncode(self, payloadBytes):
        crc = self.crc(payloadBytes)
        crcBytes = self.crcBytes(payloadBytes)
        return "%s%s" % (payloadBytes, crcBytes)

    def packetDecode(self, packetBytes):
        if len(packetBytes) <= 2:
            raise ValueError("bad packet len %d" % len(packetBytes))
        crc = self.extractCrc(packetBytes)
        payloadBytes = packetBytes[0 : - 2]
        if not self.crcCheck(payloadBytes, crc):
            raise ValueError("mismatched CRC")
        return payloadBytes

    def cobsEncode(self, data):
        return cobs.encode(data)

    def cobsDecode(self, data):
        return cobs.decode(data)

    def serialEncode(self, payloadBytes):
        return self.cobsEncode(self.packetEncode(payloadBytes))

    def serialDecode(self, serialBytes):
        if len(serialBytes) <= 2:
            raise ValueError("bad serial len %d" % len(serialBytes))
        return self.packetDecode(self.cobsDecode(serialBytes))
