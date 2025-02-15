#!/usr/bin/env python
#
# Serial pins for simulavr
#
# Copyright (C) 2019  Joel Truher (Google LLC)
# Copyright (C) 2015  Kevin O'Connor
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import pysimulavr, sys
import binascii
import datetime

SERIALBITS = 10 # 8N1 = 1 start, 8 data, 1 stop

# Class to read serial data from AVR serial transmit pin.
class DebugSerialRxPin(pysimulavr.PySimulationMember, pysimulavr.Pin):
    def __init__(self, baud):
        pysimulavr.Pin.__init__(self)
        pysimulavr.PySimulationMember.__init__(self)
        self.sc = pysimulavr.SystemClock.Instance()
        self.delay = 10**9 / baud   # ns to wait?
        self.current = 0
        self.pos = -1
        self.buffer = ""

    # overrides Pin.SetInState()
    def SetInState(self, pin):
        pysimulavr.Pin.SetInState(self, pin)
        self.state = pin.outState
        if self.pos < 0 and pin.outState == pin.LOW:
            self.pos = 0
            self.sc.Add(self)

    # overrides PySimulationMember.DoStep()
    def DoStep(self, trueHwStep):
        ishigh = self.state == self.HIGH
        self.current |= ishigh << self.pos
        self.pos += 1
        if self.pos == 1:
            return int(self.delay * 1.5)
        if self.pos >= SERIALBITS:
            newChar = chr((self.current >> 1) & 0xff)
            sys.stderr.write(newChar)
            sys.stderr.flush()
            self.buffer += newChar
            self.pos = -1
            self.current = 0
            return -1  # this means "don't call anymore"
        return self.delay

    def ClearBuffer(self):
        self.buffer = ""

    def GetBuffer(self):
        return self.buffer

# Class to read serial data from AVR serial transmit pin.
class SerialRxPin(pysimulavr.PySimulationMember, pysimulavr.Pin):
    def __init__(self, baud, dumpfile):
        pysimulavr.Pin.__init__(self)
        pysimulavr.PySimulationMember.__init__(self)
        self.sc = pysimulavr.SystemClock.Instance()
        self.delay = 10**9 / baud   # ns to wait?
        self.current = 0
        self.pos = -1
        self.queue = ""
        self.dumpfile = dumpfile
        self.dumpfile.write("START SERIAL RX DUMP\n")
        self.dumpfile.flush()

    # overrides Pin.SetInState()
    def SetInState(self, pin):
        pysimulavr.Pin.SetInState(self, pin)
        self.state = pin.outState
        if self.pos < 0 and pin.outState == pin.LOW:
            self.pos = 0
            self.sc.Add(self)

    # overrides PySimulationMember.DoStep()
    def DoStep(self, trueHwStep):
        ishigh = self.state == self.HIGH
        self.current |= ishigh << self.pos
        self.pos += 1
        if self.pos == 1:
            return int(self.delay * 1.5)
        if self.pos >= SERIALBITS:
            newchr = chr((self.current >> 1) & 0xff)
            self.queue += newchr

            self.dumpfile.write("RX %s %d %s\n" % (str(datetime.datetime.now()), self.sc.GetCurrentTime(), binascii.hexlify(newchr)))
            self.dumpfile.flush()

            self.pos = -1
            self.current = 0
            return -1  # this means "don't call anymore"
        return self.delay

    def popChars(self):
        d = self.queue
        self.queue = ""
        return d

# Class to send serial data to AVR serial receive pin.
class SerialTxPin(pysimulavr.PySimulationMember, pysimulavr.Pin):
    def __init__(self, baud, dumpfile):
        pysimulavr.Pin.__init__(self)
        pysimulavr.PySimulationMember.__init__(self)
        self.SetPin('H')
        self.sc = pysimulavr.SystemClock.Instance()
        self.delay = 10**9 / baud
        self.current = 0
        self.pos = 0
        self.queue = ""
        self.dumpfile = dumpfile
        self.dumpfile.write("START SERIAL RX DUMP\n")
        self.dumpfile.flush()

    # overrides PySimulationMember.DoStep()
    def DoStep(self, trueHwStep):
        if not self.pos:
            if not self.queue:
                return -1  # this means "don't call anymore"
            newchr = self.queue[0]
            self.dumpfile.write("TX %s %s\n" % (str(datetime.datetime.now()), binascii.hexlify(newchr)))
            self.dumpfile.flush()
            self.current = (ord(self.queue[0]) << 1) | 0x200
            self.queue = self.queue[1:]
        newstate = 'L'
        if self.current & (1 << self.pos):
            newstate = 'H'
        self.SetPin(newstate)
        self.pos += 1
        if self.pos >= SERIALBITS:
            self.pos = 0
        return self.delay

    def pushChars(self, c):
        queueEmpty = not self.queue
        self.queue += c
        if queueEmpty:
            self.sc.Add(self)
