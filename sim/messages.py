#!/usr/bin/env python
#
# domain objects and memory layout (packing) to match arduino structs
# TODO: some sort of superclass

#import collections
import struct
import codec


class Request:
    requestStruct = struct.Struct("<BBB")
    mycodec = codec.Codec()

    def __init__(self, a, b, c):
        self.a = a # uchar
        self.b = b # uchar
        self.c = c # uchar

    def __str__(self):
        return "a: %d, b: %d, c: %d" % (self.a, self.b, self.c)

    # returns bytes
    def pack(self):
        return Request.requestStruct.pack(self.a, self.b, self.c)

    # returns an object
    @staticmethod
    def unpack(packed):
        return Request(*(Request.requestStruct.unpack(packed))) # star means "unroll"

    # to and from cobs-encoded (zero-delimited) packets
    def toSerial(self):
        return Request.mycodec.serialEncode(self.pack())

    @staticmethod
    def fromSerial(serialBytes):
        if len(serialBytes) <= 2:
            raise ValueError("bad serial len %d" % len(serialBytes))
        return Request.unpack(Request.mycodec.serialDecode(serialBytes))

class Response:
    responseStruct = struct.Struct("<BB")
    mycodec = codec.Codec()

    def __init__(self, x, y):
        self.x = x # uchar
        self.y = y # uchar

    def __str__(self):
        return "x: %d, y: %d" % (self.x, self.y)

    # returns bytes
    def pack(self):
        return Response.responseStruct.pack(self.x, self.y)

    # returns an object
    @staticmethod
    def unpack(packed):
        return Response(*(Response.responseStruct.unpack(packed))) # star means "unroll"

    def toSerial(self):
        return Response.mycodec.serialEncode(self.pack())

    @staticmethod
    def fromSerial(serialBytes):
        if len(serialBytes) <= 2:
            raise ValueError("bad serial len %d" % len(serialBytes))
        return Response.unpack(Response.mycodec.serialDecode(serialBytes))
