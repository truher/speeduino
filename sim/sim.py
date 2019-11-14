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
from output import OutputPin
from inputs import InputPin
from vr import CrankVrPin, CamVrPin
from crank import Crank
import pysimulavr
import binascii

# this dumps the whole entire eeprom to the console, which verifies
# that it actually has the right thing in it, but it's hard to read :-)
def dumpEeprom(dev):
    myEeprom = dev.eeprom
    b = bytearray()
    for x in range(4095):   # 4096 bytes in EEPROM
        b.extend(chr(myEeprom.ReadFromAddress(x)))
    sys.stdout.write("eeprom: \n%s\n" % binascii.hexlify(b))

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
    # it adds and removes itself from the sim stepper
    rxpin = SerialRxPin(baud)
    netD1 = pysimulavr.Net()
    netD1.Add(rxpin)
    netD1.Add(dev.GetPin("E1"))  # mega2560 TX0 pin

    # TX pin, i.e. what avr thinks "RX" is
    # it adds and removes itself from the sim stepper
    txpin = SerialTxPin(baud)
    netD0 = pysimulavr.Net()
    netD0.Add(txpin)
    netD0.Add(dev.GetPin("E0"))  # mega2560 RX0 pin

    # Named pipe for TunerStudio
    pipe = Pipe(ptyname, speed, rxpin, txpin)
    # runs all the time
    sc.Add(pipe)

    myEeprom = dev.eeprom
    # it has 4096 bytes.
    sys.stdout.write("eeprom size %d\n" % myEeprom.GetSize())
    sys.stdout.write("DATA VERSION %d\n" % myEeprom.ReadFromAddress(0))

    crank = Crank(1000, 1)
    # runs all the time
    sc.Add(crank)
    

    # inputs

    tach1 = CrankVrPin(crank)
    sc.Add(tach1)
    netD19 = pysimulavr.Net()
    netD19.Add(tach1)
    netD19.Add(dev.GetPin("D2"))

    tach2 = CamVrPin(crank)
    sc.Add(tach2)
    netD18 = pysimulavr.Net()
    netD19.Add(tach2)
    netD19.Add(dev.GetPin("D3"))

    # i think tps is just linear, 0-5 = 0-90, but i'm not sure.
    tps = InputPin()
    tps.SetAnalogValue(0.1)
    sc.Add(tps)
    netA2 = pysimulavr.Net()
    netA2.Add(tps)
    netA2.Add(dev.GetPin("F2"))

    # the map transfer function is.
    # Vout = 5.1 * (0.00369*P + 0.04)
    # https://www.mouser.com/datasheet/2/302/MPX4250-1127330.pdf
    mapPin = InputPin()
    mapPin.SetAnalogValue(1.0)
    sc.Add(mapPin)
    netA3 = pysimulavr.Net()
    netA3.Add(mapPin)
    netA3.Add(dev.GetPin("F3"))

    # iat is a resistance measurement with 2.49k bias.
    # don't want that, use 0.5v.  where's the calibration?
    iat = InputPin()
    iat.SetAnalogValue(1.0)
    sc.Add(iat)
    netA0 = pysimulavr.Net()
    netA0.Add(iat)
    netA0.Add(dev.GetPin("F0"))

    # clt is a resistance measurement with 2.49k bias.
    # don't want that, use 0.5v.  where's the calibration?
    clt = InputPin()
    clt.SetAnalogValue(1.0)
    sc.Add(clt)
    netA1 = pysimulavr.Net()
    netA1.Add(clt)
    netA1.Add(dev.GetPin("F1"))

    # AFR = (2.3750 * Volts) + 7.3125, so Volts = (AFR - 7.3125) / 2.3750
    # https://www.aemelectronics.com/files/instructions/30-0310%20X-Series%20Inline%20Wideband%20UEGO%20Sensor%20Controller.pdf
    o2 = InputPin()
    o2.SetAnalogValue(2.5)
    sc.Add(o2)
    netA8 = pysimulavr.Net()
    netA8.Add(o2)
    netA8.Add(dev.GetPin("K0"))

    # 12v through 3.9/1 divider => 12.7v becomes 2.6v
    bat = InputPin()
    bat.SetAnalogValue(2.6)
    sc.Add(bat)
    netA4 = pysimulavr.Net()
    netA4.Add(bat)
    netA4.Add(dev.GetPin("F4"))

    # outputs
    # do not need Stepping

    inj1 =  OutputPin()
    netD8 = pysimulavr.Net()
    netD8.Add(inj1)
    netD8.Add(dev.GetPin("H5"))
    inj2 =  OutputPin()
    netD9 = pysimulavr.Net()
    netD9.Add(inj2)
    netD9.Add(dev.GetPin("H6"))
    inj3 =  OutputPin()
    netD10 = pysimulavr.Net()
    netD10.Add(inj3)
    netD10.Add(dev.GetPin("B4"))
    inj4 =  OutputPin()
    netD11 = pysimulavr.Net()
    netD11.Add(inj4)
    netD11.Add(dev.GetPin("B5"))

    ign1 =  OutputPin()
    netD40 = pysimulavr.Net()
    netD40.Add(ign1)
    netD40.Add(dev.GetPin("G1"))
    ign2 =  OutputPin()
    netD38 = pysimulavr.Net()
    netD38.Add(ign2)
    netD38.Add(dev.GetPin("D7"))
    ign3 =  OutputPin()
    netD52 = pysimulavr.Net()
    netD52.Add(ign3)
    netD52.Add(dev.GetPin("B1"))
    ign4 =  OutputPin()
    netD50 = pysimulavr.Net()
    netD50.Add(ign4)
    netD50.Add(dev.GetPin("B3"))

    msg = "Starting AVR simulation: machine=%s speed=%d\n" % (proc, speed)
    msg += "Serial: port=%s baud=%d\n" % (ptyname, baud)
    sys.stdout.write(msg)
    sys.stdout.flush()

    # Run forever
    while 1:
        #sc.Endless()
        sc.RunTimeRange(speed/10)
        #sys.stdout.write("time %d\n" % sc.GetCurrentTime())

        # in 2560 it's uint8 byte
        #tppp = dev.data.GetAddressAtSymbol("triggerPri_pin_port")
        #sys.stdout.write("triggerPri_pin_port: %d\n" % dev.getRWMem(tppp))
        #sys.stdout.write("triggerPri_pin_port (hex): %X\n" % dev.getRWMem(tppp))

        # total runtime
        # this is how you get stuff out of structs, it's by offset.
        #cs = dev.data.GetAddressAtSymbol("currentStatus")
        #sys.stdout.write("currentStatus.runSecs: %d\n" % dev.getRWMem(cs+93))

        # loops this second
        #mlc = dev.data.GetAddressAtSymbol("mainLoopCount")
        #sys.stdout.write("mainLoopCount: %d\n" % (dev.getRWMem(mlc) + (dev.getRWMem(mlc+1) << 8)))

        #sys.stdout.write("crank angle: %d crank: %s cam: %s\n" % (crank.currentAngleDegrees, tach1.state, tach2.state))

        #sys.stdout.write("sync: %s\n" % binascii.hexlify(chr(dev.getRWMem(addr))))
        #sys.stdout.write("runSecs: %s\n" % binascii.hexlify(chr(dev.getRWMem(addr+95))))
        #sys.stdout.write("secl: %s\n" % binascii.hexlify(chr(dev.getRWMem(addr+96))))
        #sys.stdout.write("\n\n\n")
        #sys.stdout.write("DATA VERSION %d\n" % myEeprom.ReadFromAddress(0))
        #dumpEeprom(dev)

if __name__ == '__main__':
    main()
