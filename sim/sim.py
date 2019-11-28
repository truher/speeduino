#!/usr/bin/env python
#
# Speeduino Simulator
#
# Copyright (C) 2019  Joel Truher (Google LLC)
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import sys, optparse
from serial import SerialRxPin, SerialTxPin, DebugSerialRxPin
from pipe import Pipe
from output import OutputPin
from inputs import InputPin
from vr import CrankVrPin, CamVrPin
from crank import Crank
import pysimulavr
import binascii
import dwarf

class SimMemory(dwarf.Memory):
    def __init__(self, dev):
        self.dev = dev
    def get(self, addr):
        val = self.dev.getRWMem(addr)
        #print "get addr %d val %d" % (addr, val)
        return val
    def set(self, addr, val):
        #print "set addr %d val %d" % (addr, val)
        self.dev.setRWMem(addr, val)

# this dumps the whole entire eeprom to the console, which verifies
# that it actually has the right thing in it, but it's hard to read :-)
def dumpEeprom(dev):
    myEeprom = dev.eeprom
    #b = bytearray()
    #for x in range(4095):   # 4096 bytes in EEPROM
    #for x in range(709,837):
        #b.extend(chr(myEeprom.ReadFromAddress(x)))
        #b.extend(chr(myEeprom.GetMemory(x)))
    #sys.stdout.write("eeprom: \n%s\n" % binascii.hexlify(b))
    for ost in range(709,837):
        test_str = chr(myEeprom.ReadFromAddress(ost))
        #sys.stdout.write("eeprom:%d: %s\n" % (ost, ''.join(format(ord(i), '08b') for i in test_str)))


#def writeEeprom(dev):
#    EEPROM_CONFIG4_START = 709
#    myEeprom = dev.eeprom
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 0, 36) # 00100100
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 1, 0)
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 2, 22) # 00010110
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 3, 53) # 00110101

def printPins(dev):
    # pins, these don't change
    sys.stdout.write("pinTrigger: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinTrigger"))))
    sys.stdout.write("pinTrigger2: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinTrigger2"))))
    sys.stdout.write("pinTPS: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinTPS"))))
    sys.stdout.write("pinMAP: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinMAP"))))
    sys.stdout.write("pinIAT: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinIAT"))))
    sys.stdout.write("pinCLT: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinCLT"))))
    sys.stdout.write("pinO2: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinO2"))))
    sys.stdout.write("pinBat: %d\n" % (dev.getRWMem(dev.data.GetAddressAtSymbol("pinBat"))))


def main():
    usage = "%prog [options] <program.elf>"
    opts = optparse.OptionParser(usage)
    #opts.add_option("-p", "--port", type="string", dest="port",
    #                default="/tmp/pseudoserial",
    #                help="pseudo-tty device to create for serial port")
    options, args = opts.parse_args()
    if len(args) != 1:
        opts.error("Incorrect number of arguments")
    filename = args[0]
    ptyname = '/tmp/pseudoserial' # options.port
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
    dev.Load(filename)
    dev.SetClockFreq(10**9 / speed)
    sc.Add(dev)

    mem = SimMemory(dev)

    cu_name = 'speeduino/speeduino.ino.cpp'
    variables = dwarf.Globals(mem, filename, cu_name)

    #os = pysimulavr.ostringstream()
    #pysimulavr.DumpManager.Instance().save(os)
    #foo = filter(None, [i.strip() for i in os.str().split("\n")])
    #print "all registrered trace values:\n ",
    #print "\n  ".join(foo)
#
#    signals = (
#            "PORTD.D2-Out",
#            "PORTD.D3-Out"
#           )
#    sigs = ["+ " + i for i in signals]
#    pysimulavr.DumpManager.Instance().addDumpVCD("out.vcd", "\n".join(sigs), "ns", False, False)
#


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





    rxpin2 = DebugSerialRxPin(baud)
    netH1 = pysimulavr.Net()
    netH1.Add(rxpin2)
    netH1.Add(dev.GetPin("H1"))  # mega2560 TX0 pin





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
    netA3.Add(dev.GetPin("A3"))
    #netA3.Add(dev.GetPin("A0"))
    #netA3.Add(dev.GetPin("F3"))

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
    #netA4.Add(dev.GetPin("F4"))
    netA4.Add(dev.GetPin("A4"))

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

    #dm = pysimulavr.DumpManager.Instance()
    #d = pysimulavr.DumpVCD("out.vcd")
    ##dumper.setActiveSignals
    #sigs = ("+ PORTD.PIN\n"
    #        "+ PORTE.PIN\n"
    #        "+ PORTF.PIN\n"
    #       )
    ##vals = dm.all()
    #dm.addDumper(d, dm.load(sigs))
    #dm.start()
#
#
#    printPins(dev)

    # wiring done
    # configure

    
    # this doesn't work because it loads from EEPROM
    # so i need to stuff it into eeprom .. some parts of
    # the eprom are just copies of the config strucs though.
    EEPROM_CONFIG4_START = 709
    EEPROM_CONFIG4_END =   837
    myEeprom = dev.eeprom
#    dumpEeprom(dev)
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 0, 0) # configPage4.triggerAngle
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 1, 0)
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 2, 0)
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 3, 0)
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 9, 0) # configPage4.TrigSpeed
#    #myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 11, c_ubyte(5)) # configPage4.trigPattern
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 11, 5) # configPage4.trigPattern
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 16, 0) # configPage4.TrigPatternSec
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 21, 0) # configPage4.StgCycles
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 24, 3) # configPage4.sparkMode
##    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 25, 2) # configPage4.triggerFilter
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 29, 36) # configPage4.triggerTeeth
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 30, 1) # configPage4.triggerMissingTeeth
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 31, 40) # configPage4.crankRPM (/10)


#    writeEeprom(dev)
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 0, 36) # 00100100
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 1, 0)
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 2, 22) # 00010110
#    myEeprom.WriteAtAddress(EEPROM_CONFIG4_START + 3, 53) # 00110101
    sys.stdout.write("S0 new\n")
    # at this point the configPage4 struct is uninitialized
    #print("configPage2 %d" % dev.data.GetAddressAtSymbol("configPage2"))
    print("configPage4 %d" % dev.data.GetAddressAtSymbol("configPage4"))
    print("configPage6 %d" % dev.data.GetAddressAtSymbol("configPage6"))
    print("configPage9 %d" % dev.data.GetAddressAtSymbol("configPage9"))

    print "=========================================="
    print("configPage9 %d" % dev.data.GetAddressAtSymbol("fpPrimeTime"))
    print("mainLoopCount %d" % dev.data.GetAddressAtSymbol("mainLoopCount"))
    print("revolutionTime %d" % dev.data.GetAddressAtSymbol("revolutionTime"))
    print("clutchTrigger %d" % dev.data.GetAddressAtSymbol("clutchTrigger"))
    print "=========================================="

    #mem = SimMemory(dev)
    #variables = dwarf.Globals(mem, filename, 'speeduino/speeduino.ino.cpp')
    configPage4 = variables.variable('configPage4')
    currentStatus = variables.variable('currentStatus')
    sys.stdout.write("NEW configPage4.triggerAngle: %d\n" % configPage4.member('triggerAngle').read())
    sys.stdout.write("NEW configPage4.FixAng: %d\n" % configPage4.member('FixAng').read())
    sys.stdout.write("NEW configPage4.CrankAng: %d\n" % configPage4.member('CrankAng').read())
    sys.stdout.write("NEW configPage4.TrigAngMul: %d\n" % configPage4.member('TrigAngMul').read())
    sys.stdout.write("NEW configPage4.TrigEdge: %d\n" % configPage4.member('TrigEdge').read())


    configPage4.member('triggerAngle').write(36)
    configPage4.member('FixAng').write(22)
    configPage4.member('CrankAng').write(53)
    configPage4.member('TrigAngMul').write(121)
    configPage4.member('TrigEdge').write(21)

    sys.stdout.write("S0 write\n")
    # write everything to eeprom
    for x in range(EEPROM_CONFIG4_START, EEPROM_CONFIG4_END):
        configPage4 = variables.variable('configPage4')
        eeprom_relative = x - EEPROM_CONFIG4_START
        var_relative = configPage4.location() + x - EEPROM_CONFIG4_START
        val = mem.get(var_relative)
        #print "addr %d val %d " % (x, val)
        dev.eeprom.WriteAtAddress(x, val)

    sys.stdout.write("S0 dump\n")
    configPage4.member('triggerAngle').write(36)
    configPage4.member('FixAng').write(22)
    configPage4.member('CrankAng').write(53)
    configPage4.member('TrigAngMul').write(121)
    configPage4.member('TrigEdge').write(21)
    sys.stdout.write("S0 dump eeprom\n")
    dumpEeprom(dev)
    sys.stdout.write("S0 done\n")
    # Run forever
   # while 1:
    for cy in range(10):
        sys.stdout.write("NEW currentStatus.hasSync: %d\n" % currentStatus.member('hasSync').read())
        sys.stdout.write("NEW currentStatus.RPM: %d\n" % currentStatus.member('RPM').read())
        #d.cycle()  # Step() in avrdevice does this
        #sc.Endless()
        # struct has not been read from eeprom yet, so this shows uninitialized
        sys.stdout.write("S1 run\n")
        sc.RunTimeRange(speed)
        sys.stdout.write("S1 done\n")
        sys.stdout.write("S2 dump\n")
        sys.stdout.write("NEW1 configPage4.triggerAngle: %d\n" % configPage4.member('triggerAngle').read())
        sys.stdout.write("NEW1 configPage4.FixAng: %d\n" % configPage4.member('FixAng').read())
        sys.stdout.write("NEW1 configPage4.CrankAng: %d\n" % configPage4.member('CrankAng').read())
        sys.stdout.write("NEW1 configPage4.TrigAngMul: %d\n" % configPage4.member('TrigAngMul').read())
        sys.stdout.write("NEW1 configPage4.TrigEdge: %d\n" % configPage4.member('TrigEdge').read())

        sys.stdout.write("S2 done\n")
        #exit()
        #sys.stdout.write("time %d\n" % sc.GetCurrentTime())

        # in 2560 it's uint8 byte
        #tppp = dev.data.GetAddressAtSymbol("triggerPri_pin_port")
        #sys.stdout.write("triggerPri_pin_port: %d\n" % dev.getRWMem(tppp))
        #sys.stdout.write("triggerPri_pin_port (hex): %X\n" % dev.getRWMem(tppp))

        # globals

        sys.stdout.write("ignitionOn: %d\n" % variables.variable('ignitionOn').read())
        sys.stdout.write("fuelOn: %d\n" % variables.variable("fuelOn").read())
        sys.stdout.write("mapErrorCount: %d\n" % variables.variable("mapErrorCount").read())
        sys.stdout.write("MAPcount: %d\n" % variables.variable("MAPcount").read())
        sys.stdout.write("MAPrunningValue: %d\n" % variables.variable("MAPrunningValue").read())
        sys.stdout.write("MAPlast: %d\n" % variables.variable("MAPlast").read())
        sys.stdout.write("revolutionTime: %d\n" % variables.variable("revolutionTime").read())
        sys.stdout.write("toothCurrentCount: %d\n" % variables.variable("toothCurrentCount").read())
        sys.stdout.write("toothOneTime: %d\n" % variables.variable("toothOneTime").read())
        sys.stdout.write("toothLastToothTime: %d\n" % variables.variable("toothLastToothTime").read())
        sys.stdout.write("toothOneMinusOneTime: %d\n" % variables.variable("toothOneMinusOneTime").read())
        sys.stdout.write("triggerToothAngleIsCorrect: %d\n" % variables.variable("triggerToothAngleIsCorrect").read())

        # currentStatus
        sys.stdout.write("currentStatus.hasSync: %d\n" % currentStatus.member("hasSync").read())
        sys.stdout.write("currentStatus.RPM: %d\n" % currentStatus.member("RPM").read())
        sys.stdout.write("currentStatus.longRPM: %d\n" %currentStatus.member("longRPM").read())
        sys.stdout.write("currentStatus.mapADC: %d\n" %currentStatus.member("mapADC").read())
        sys.stdout.write("currentStatus.baroADC: %d\n" %currentStatus.member("baroADC").read())
        sys.stdout.write("currentStatus.MAP: %d\n" %currentStatus.member("MAP").read())
        sys.stdout.write("currentStatus.baro: %d\n" % currentStatus.member("baro").read())
        sys.stdout.write("currentStatus.TPS: %d\n" % currentStatus.member("TPS").read())
        sys.stdout.write("currentStatus.tpsADC: %d\n" % currentStatus.member("tpsADC").read())
        sys.stdout.write("currentStatus.VE: %d\n" % currentStatus.member("VE").read())
        sys.stdout.write("currentStatus.VE1: %d\n" % currentStatus.member("VE1").read())
        sys.stdout.write("currentStatus.tpsADC: %d\n" % currentStatus.member("tpsADC").read())
        sys.stdout.write("currentStatus.coolant: %d\n" % currentStatus.member("coolant").read())
        sys.stdout.write("currentStatus.cltADC: %d\n" % currentStatus.member("cltADC").read())
        sys.stdout.write("currentStatus.iatADC: %d\n" % currentStatus.member("iatADC").read())
        sys.stdout.write("currentStatus.batADC: %d\n" % currentStatus.member("batADC").read())
        sys.stdout.write("currentStatus.O2ADC: %d\n" % currentStatus.member("O2ADC").read())
        sys.stdout.write("currentStatus.egoCorrection: %d\n" % currentStatus.member("egoCorrection").read())
        ## total runtime
        sys.stdout.write("currentStatus.runSecs: %d\n" % currentStatus.member("runSecs").read())

        # configPage4
        sys.stdout.write("NEW1 configPage4.triggerAngle: %d\n" % configPage4.member('triggerAngle').read())
        sys.stdout.write("NEW1 configPage4.FixAng: %d\n" % configPage4.member('FixAng').read())
        sys.stdout.write("NEW1 configPage4.CrankAng: %d\n" % configPage4.member('CrankAng').read())
        sys.stdout.write("NEW1 configPage4.TrigAngMul: %d\n" % configPage4.member('TrigAngMul').read())
        sys.stdout.write("NEW1 configPage4.TrigEdge: %d\n" % configPage4.member('TrigEdge').read())
        sys.stdout.write("NEW1 configPage4.TrigSpeed: %d\n" % configPage4.member('TrigSpeed').read())
        sys.stdout.write("NEW1 configPage4.IgInv: %d\n" % configPage4.member('IgInv').read())
        sys.stdout.write("NEW1 configPage4.TrigPattern: %d\n" % configPage4.member('TrigPattern').read())
        sys.stdout.write("NEW1 configPage4.StgCycles: %d\n" % configPage4.member('StgCycles').read())
        sys.stdout.write("NEW1 configPage4.sparkMode: %d\n" % configPage4.member('sparkMode').read())
        sys.stdout.write("NEW1 configPage4.triggerFilter: %d\n" % configPage4.member('triggerFilter').read())
        sys.stdout.write("NEW1 configPage4.triggerTeeth: %d\n" % configPage4.member('triggerTeeth').read())
        sys.stdout.write("NEW1 configPage4.triggerMissingTeeth: %d\n" % configPage4.member('triggerMissingTeeth').read())
        sys.stdout.write("NEW1 configPage4.crankRPM: %d\n" % configPage4.member('crankRPM').read())

        #cp6 = dev.data.GetAddressAtSymbol("configPage6")
        #cp9 = dev.data.GetAddressAtSymbol("configPage9")
        #cp10 = dev.data.GetAddressAtSymbol("configPage10")




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

#        for ost in range(64):
#            cs = dev.data.GetAddressAtSymbol("configPage4")
#            test_str = chr(dev.getRWMem(cs+ost))
#            sys.stdout.write("configPage4:%d: %s\n" % (ost, ''.join(format(ord(i), '08b') for i in test_str)))

        #for ost in range(64):
        #    cs = dev.data.GetAddressAtSymbol("configPage4")
        #    #sys.stdout.write("configPage4:%d: %s\n" % (ost,hex(dev.getRWMem(cs+ost))))
        #    test_str = chr(dev.getRWMem(cs+ost))
        #    sys.stdout.write("configPage4:%d: %s\n" % (ost, ''.join(format(ord(i), '08b') for i in test_str)))
        #for ost in range(150):
        #    cs = dev.data.GetAddressAtSymbol("currentStatus")
        #    sys.stdout.write("currentStatus:%d: %s\n" % (ost,hex(dev.getRWMem(cs+ost))))

    #d.stop()

if __name__ == '__main__':
    main()
