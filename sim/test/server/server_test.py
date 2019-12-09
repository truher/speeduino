import sys
sys.path.append("../..")
import server
import codec
import messages

import unittest
import pysimulavr
import test_client
import server
import time
import datetime
import types
import struct

class ServerTest(unittest.TestCase):

    def testDirect(self):
        ptyname = "/tmp/testclient"
        myclient = test_client.Client(ptyname)
        myserver = server.Server(ptyname)
        myserver.run()

        reqBytes = messages.Request(0,2,0).toSerial()
        resBytes = myclient.rpc(reqBytes)
        res = messages.Response.fromSerial(resBytes)
        self.assertEqual(0, res.x)
        self.assertEqual(6, res.y)

    def testDirectPerformance(self):
        ptyname = "/tmp/testclient"
        myclient = test_client.Client(ptyname)
        myserver = server.Server(ptyname)
        myserver.run()

        iterations = 30000
        t0 = datetime.datetime.now()
        for i in range(0, iterations):
            j = i % 80
            req = messages.Request(0,j,0)
            reqBytes = req.toSerial()
            resBytes = myclient.rpc(reqBytes)
            res = messages.Response.fromSerial(resBytes)
            self.assertEqual(0, res.x)
            self.assertEqual(3 * j, res.y)
        t1 = datetime.datetime.now()
        td = t1 - t0
        us_per_iter = td.total_seconds() * 1000000 / iterations
        print "round trip us per iter %f" % us_per_iter # about 36 us per round-trip

    def testCrc(self):
        message = "hello"
        mycodec = codec.Codec()
        crc = mycodec.crc(message)
        self.assertEqual(types.IntType, type(crc))
        self.assertEqual(50018, crc)  # https://crccalc.com/
        self.assertTrue(mycodec.crcCheck(message, crc))

    def testReq(self):
        req = messages.Request(1,2,3)
        reqstr = req.pack()
        self.assertEqual("\x01\x02\x03", reqstr)
        req2 = messages.Request.unpack(reqstr)
        self.assertEqual(1, req2.a)
        self.assertEqual(2, req2.b)
        self.assertEqual(3, req2.c)

    def testRes(self):
        res = messages.Response(1,2)
        resstr = res.pack()
        self.assertEqual("\x01\x02", resstr)
        res2 = messages.Response.unpack(resstr)
        self.assertEqual(1, res2.x)
        self.assertEqual(2, res2.y)

    def testCrcBytes(self):
        mycodec = codec.Codec()
        myCrcBytes = mycodec.crcBytes("hello")
        self.assertEqual(2, len(myCrcBytes))
        self.assertEqual(types.StringType, type(myCrcBytes))
        self.assertEqual("\x62\xc3", myCrcBytes)

    def testPack(self):
        crc = 50018
        myCrcBytes = struct.pack("<H", crc)
        self.assertEqual(types.StringType, type(myCrcBytes))
        self.assertEqual("\x62\xc3", myCrcBytes)
 
    def testEncoder(self):
        mycodec = codec.Codec()
        req = messages.Request(1,2,3)
        payloadBytes = req.pack()
        mypacket = mycodec.packetEncode(payloadBytes)
        self.assertEqual("\x01\x02\x03\x31\x61", mypacket)

    def testCrcWithZeros(self):
        mycodec = codec.Codec()
        req = messages.Request(0,2,0)
        payloadBytes = req.pack()
        self.assertEqual("\x00\x02\x00", payloadBytes)
        crc = mycodec.crc(payloadBytes)
        self.assertEqual(26210, crc)

    def testCrcBytesWithZeros(self):
        mycodec = codec.Codec()
        req = messages.Request(0,2,0)
        payloadBytes = req.pack()
        self.assertEqual("\x00\x02\x00", payloadBytes)
        crcBytes = mycodec.crcBytes(payloadBytes)
        self.assertEqual("\x62\x66", crcBytes)

    def testEncoderWithZeros(self):
        mycodec = codec.Codec()
        req = messages.Request(0,2,0)
        payloadBytes = req.pack()
        mypacket = mycodec.packetEncode(payloadBytes)
        self.assertEqual("\x00\x02\x00\x62\x66", mypacket)

    def testPacketCodecWithZeros(self):
        mycodec = codec.Codec()
        req = messages.Request(0,2,0)
        payloadBytes = req.pack()
        mypacket = mycodec.packetEncode(payloadBytes)
        self.assertEqual("\x00\x02\x00\x62\x66", mypacket)
        crc = mycodec.extractCrc(mypacket)
        self.assertEqual(26210, crc)
        payloadBytes2 = mycodec.packetDecode(mypacket)
        req2 = messages.Request.unpack(payloadBytes2)
        self.assertEqual(0, req2.a)
        self.assertEqual(2, req2.b)
        self.assertEqual(0, req2.c)

    def testPacketDecodeWithError(self):
        mycodec = codec.Codec()
        with self.assertRaises(ValueError):
            payloadBytes2 = mycodec.packetDecode("\x00\x02\x01\x62\x66") # data err
        with self.assertRaises(ValueError):
            payloadBytes2 = mycodec.packetDecode("\x00\x02\x00\x61\x66") # crc err

    def testCobsEncoder(self):
        mycodec = codec.Codec()
        # prepends len+1, if no \0
        self.assertEqual("\x04\x01\x02\x02", mycodec.cobsEncode("\x01\x02\x02"))
        self.assertEqual("\x02\x01\x02\x02", mycodec.cobsEncode("\x01\x00\x02"))

    def testCobsDecoder(self):
        mycodec = codec.Codec()
        self.assertEqual("\x01\x02\x02", mycodec.cobsDecode("\x04\x01\x02\x02"))
        self.assertEqual("\x01\x00\x02", mycodec.cobsDecode("\x02\x01\x02\x02"))
 
    def testSerialEncoder(self):
        mycodec = codec.Codec()
        req = messages.Request(0,2,0)
        payloadBytes = req.pack()
        myserial = mycodec.serialEncode(payloadBytes)
        self.assertEqual("\x01\x02\x02\x03\x62\x66", myserial)

    def testSerialDecoder(self):
        mycodec = codec.Codec()
        payloadBytes = mycodec.serialDecode("\x01\x02\x02\x03\x62\x66")
        req2 = messages.Request.unpack(payloadBytes)
        self.assertEqual(0, req2.a)
        self.assertEqual(2, req2.b)
        self.assertEqual(0, req2.c)

    def testCodecEndToEnd(self):
        req = messages.Request(0,2,0)
        expected = "\x01\x02\x02\x03\x62\x66"
        self.assertEqual(expected, req.toSerial())
        req2 = messages.Request.fromSerial(expected)
        self.assertEqual(0, req2.a)
        self.assertEqual(2, req2.b)
        self.assertEqual(0, req2.c)

    def testCodecEndToEndPerformance(self):
        iterations = 250000
        t0 = datetime.datetime.now()
        for i in range(0,iterations):
            req2 = messages.Request.fromSerial(messages.Request(0,2,0).toSerial())

        t1 = datetime.datetime.now()
        td = t1 - t0
        us_per_iter = td.total_seconds() * 1000000 / iterations
        print "Codec us per iter %f" % us_per_iter # about 3 us per encode/decode


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ServerTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
