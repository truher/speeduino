#!/usr/bin/env python
#
# Speeduino Simulator
#
# Copyright (C) 2015  Kevin O'Connor
# Modified 2019 Joel Truher
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import sys, optparse
from serial import SerialRxPin, SerialTxPin
from pipe import Pipe
import pysimulavr

def main():
    usage = "%prog [options] <program.elf>"
    opts = optparse.OptionParser(usage)
    opts.add_option("-p", "--port", type="string", dest="port",
                    default="/tmp/pseudoserial",
                    help="pseudo-tty device to create for serial port")
    options, args = opts.parse_args()
    if len(args) != 1:
        opts.error("Incorrect number of arguments")
    elffile = args[0]
    ptyname = options.port
    proc = "atmega2560"
    speed = 16000000
    # TODO(truher) the actual baud rate is 115200, but arduino uses the "double speed"
    # flag, which isn't supported by simulavr, so to work around it, i set the baud rate
    # here to be half of the simulator baud rate, and it seems to work.
    # see also https://github.com/Traumflug/simulavr/issues/4
    baud = 57600 
    
    # System clock
    sc = pysimulavr.SystemClock.Instance()
    pysimulavr.DumpManager.Instance().SetSingleDeviceApp()

    # AVR device
    dev = pysimulavr.AvrFactory.instance().makeDevice(proc)
    dev.Load(elffile)
    dev.SetClockFreq(10**9 / speed)
    sc.Add(dev)

    # RX pin, i.e. what avr thinks "TX" is
    rxpin = SerialRxPin(baud)
    net = pysimulavr.Net()
    net.Add(rxpin)
    net.Add(dev.GetPin("E1"))  # mega2560 TX0 pin

    # TX pin, i.e. what avr thinks "RX" is
    txpin = SerialTxPin(baud)
    net2 = pysimulavr.Net()
    net2.Add(dev.GetPin("E0"))  # mega2560 RX0 pin
    net2.Add(txpin)

    # Named pipe for TunerStudio
    pipe = Pipe(ptyname, speed, rxpin, txpin)
    sc.Add(pipe)

    msg = "Starting AVR simulation: machine=%s speed=%d\n" % (proc, speed)
    msg += "Serial: port=%s baud=%d\n" % (ptyname, baud)
    sys.stdout.write(msg)
    sys.stdout.flush()

    # Run forever
    pysimulavr.DumpManager.Instance().start()
    sc.Endless()

if __name__ == '__main__':
    main()
