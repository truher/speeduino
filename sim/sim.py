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

EEPROM_CONFIG4_START = 709
EEPROM_CONFIG4_END =   837

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
def dumpEeprom(dev, start, end):
    for ost in range(start, end):
        test_str = chr(dev.eeprom.ReadFromAddress(ost))
        print "eeprom: %d: %s" % (ost, ''.join(format(ord(i), '08b') for i in test_str))

def dumpRAM(mem, start, end):
    for index in range(start, end):
        print "%d: %x" % (index - start, mem.get(index))

def dumpEepromHex(dev, start, end):
    for index in range(start, end):
        print "%d: %x" % (index - start, dev.eeprom.ReadFromAddress(index))

def writeConfigToEeprom(variables, mem, dev):
    for x in range(EEPROM_CONFIG4_START, EEPROM_CONFIG4_END):
        configPage4 = variables.variable('configPage4')
        eeprom_relative = x - EEPROM_CONFIG4_START
        var_relative = configPage4.location() + x - EEPROM_CONFIG4_START
        val = mem.get(var_relative)
        #print "addr %d val %d " % (x, val)
        dev.eeprom.WriteAtAddress(x, val)

def printPins(variables):
    print "=============== PINS ==============="
    vars = [ "pinTrigger",
             "pinTrigger2",
             "pinTPS",
             "pinMAP", "pinIAT",
             "pinCLT", "pinO2", "pinBat"]
    for var in vars:
        printVarVal(variables, var)

def writeDefaults(variables):
    configPage2 = variables.variable('configPage2')
    configPage2.member('pinMapping').write(3)  # for the 0.4 shield.
    configPage2.member('mapSample').write(0)  # instantaneous
    configPage2.member('tpsMin').write(0)
    configPage2.member('tpsMax').write(255)
    configPage2.member('mapMin').write(0)
    configPage2.member('mapMax').write(255)
    #configPage2.member('pinMapping').write(41)  # for the UA4C
    configPage2.member('injLayout').write(0)  # paired
    configPage4 = variables.variable('configPage4')
    configPage4.member('triggerAngle').write(36)
    configPage4.member('FixAng').write(22)
    configPage4.member('CrankAng').write(53)
    configPage4.member('TrigAngMul').write(121)
    configPage4.member('TrigEdge').write(0)    # rising
    configPage4.member('TrigSpeed').write(0)   # wheel on crank
    configPage4.member('IgInv').write(1)
    configPage4.member('TrigPattern').write(0) # missing tooth
    configPage4.member('TrigEdgeSec').write(0) # secondary rising
    configPage4.member('fuelPumpPin').write(1)
    configPage4.member('useResync').write(1)
    configPage4.member('StgCycles').write(0)   # ignition immediately
    configPage4.member('sparkMode').write(0)   # wasted
    configPage4.member('triggerFilter').write(0)   # no filter
    configPage4.member('trigPatternSec').write(0) # secondary pattern (unimplemented)
    configPage4.member('triggerTeeth').write(36)  # number of teeth (incl missing one)
    configPage4.member('triggerMissingTeeth').write(1)  # number of missing teeth
    configPage4.member('crankRPM').write(200)  # less than this is cranking
    configPage4.member('batVoltCorrect').write(0)  # no correction
    configPage4.member('ADCFILTER_TPS').write(128)
    configPage4.member('ADCFILTER_CLT').write(180)
    configPage4.member('ADCFILTER_IAT').write(180)
    configPage4.member('ADCFILTER_O2').write(128)
    configPage4.member('ADCFILTER_BAT').write(128)
    configPage4.member('ADCFILTER_MAP').write(20)
    configPage4.member('ADCFILTER_BARO').write(64)

def writeZeros(variables):
    configPage4 = variables.variable('configPage4')
    configPage4.member('triggerAngle').write(0)
    configPage4.member('FixAng').write(0)
    configPage4.member('CrankAng').write(0)
    configPage4.member('TrigAngMul').write(0)
    configPage4.member('TrigEdge').write(0)
    configPage4.member('TrigSpeed').write(0)
    configPage4.member('IgInv').write(0)
    configPage4.member('TrigPattern').write(0)
    configPage4.member('TrigEdgeSec').write(0)
    configPage4.member('fuelPumpPin').write(0)
    configPage4.member('useResync').write(0)



def printConfig(variables):
    print "========================= CONFIG2 ========================="
    configPage2 = variables.variable('configPage2')
    vars = [
            'reqFuel',
            'multiplyMAP',
            'injOpen',
            'mapSample',
            'tpsMin',
            'tpsMax',
            'mapMin',
            'mapMax'
            ]
    for var in vars:
        printMemberVal(configPage2, var)
    print "========================= CONFIG4 ========================="
    configPage4 = variables.variable('configPage4')
    vars = [ 'triggerAngle', 'FixAng', 'CrankAng', 'TrigAngMul', 'TrigEdge',
             'TrigSpeed', 'IgInv', 'TrigPattern', 'TrigEdgeSec', 'fuelPumpPin',
             'useResync', 'StgCycles', 'sparkMode', 'triggerFilter', 'triggerTeeth',
             'triggerMissingTeeth', 'crankRPM',
             'ADCFILTER_TPS',
             'ADCFILTER_CLT',
             'ADCFILTER_IAT',
             'ADCFILTER_O2',
             'ADCFILTER_BAT',
             'ADCFILTER_MAP',
             'ADCFILTER_BARO',
            ]
    for var in vars:
        printMemberVal(configPage4, var)

def printVarVal(variables, name):
    print "%26s: %8d" % (name, variables.variable(name).read())

def printMemberVal(variable, name):
    print "%26s: %8d" % (name, variable.member(name).read())

def printFullStatus(variables):
    print "========================= FULL STATUS ========================="
    vars = currentStatus.getAllMemberNames()
    for var in vars:
        printMemberVal(currentStatus, var)

def printStatus(variables):
    print "========================= STATUS ========================="
    currentStatus = variables.variable('currentStatus')
    vars = [
             "engine",  # bits
             "status1", # bits
             "startRevolutions",
             "hasSync",
             "syncLossCounter",
             "RPM", "longRPM", "mapADC", "baroADC",
             "MAP",
             "baro", 
             "TPS", "tpsADC", "VE", "VE1", "O2",
             "tpsADC",
             "coolant",    # +40 deg
             "cltADC", "iatADC", "batADC", "O2ADC",
             "battery10",  # volts * 10, i.e. 125 is normal
             "egoCorrection",
             "runSecs", "secl",
             "loopsPerSecond",
             "freeRAM"
            ]
    for var in vars:
        printMemberVal(currentStatus, var)

def printVars(variables):
    print "========================= VARIABLES ========================="
    vars = [ 
             "currentLoopTime",   # start of the current loop
             "previousLoopTime",  # start of the previous loop
             "curGap",
             "toothLastToothTime",
             "toothLastMinusOneToothTime",
             "toothOneTime",
             "toothOneMinusOneTime",
             "targetGap",
             "validTrigger",
             "triggerFilterTime",
             "fpPrimeTime", "mainLoopCount", "revolutionTime", "clutchTrigger",
             'ignitionOn', "fuelOn",
             "mapErrorCount",
             "iatErrorCount",
             "cltErrorCount",
             "MAPcount", "MAPrunningValue",
             "MAPlast", "toothCurrentCount",
             "triggerToothAngleIsCorrect",
             "jt_foo"
             ]
    # "triggerPri_pin_port" # TODO: implement pointers 
    for var in vars:
        printVarVal(variables, var)

def printDebugStream(pin):
    print "========================= DEBUG STREAM ========================="
    print pin.GetBuffer()
    pin.ClearBuffer()

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

    # it has 4096 bytes.
    print "eeprom size %d" % dev.eeprom.GetSize()
    print "DATA VERSION %d" % dev.eeprom.ReadFromAddress(0)

    crank = Crank(1000, 1)
    # runs all the time
    sc.Add(crank)
    

    # inputs

    tach1 = CrankVrPin(crank, sc)
    sc.Add(tach1)
    netD19 = pysimulavr.Net()
    netD19.Add(tach1)
    netD19.Add(dev.GetPin("D2")) # pin 19 = PD2 = interrupt 4?

    tach2 = CamVrPin(crank, sc)
    sc.Add(tach2)
    netD18 = pysimulavr.Net()
    netD18.Add(tach2)
    netD18.Add(dev.GetPin("D3")) # pin 18 = PD3 = interrupt 5?  6?

    # i think tps is just linear, 0-5 = 0-90, but i'm not sure.
    tps = InputPin(sc, 'tps')
    tps.SetAnalogValue(0.1)
    sc.Add(tps)
    netA2 = pysimulavr.Net()
    netA2.Add(tps)
    netA2.Add(dev.GetPin("F2"))

    # the map transfer function is.
    # Vout = 5.1 * (0.00369*P + 0.04)
    # https://www.mouser.com/datasheet/2/302/MPX4250-1127330.pdf
    mapPin = InputPin(sc, 'map')
    mapPin.SetAnalogValue(1.0)
    sc.Add(mapPin)
    netA3 = pysimulavr.Net()
    netA3.Add(mapPin)
    netA3.Add(dev.GetPin("A3"))
    #netA3.Add(dev.GetPin("A0"))
    #netA3.Add(dev.GetPin("F3"))

    # iat is a resistance measurement with 2.49k bias.
    # don't want that, use 0.5v.  where's the calibration?
    iat = InputPin(sc, 'iat')
    iat.SetAnalogValue(1.0)
    sc.Add(iat)
    netA0 = pysimulavr.Net()
    netA0.Add(iat)
    netA0.Add(dev.GetPin("F0"))

    # clt is a resistance measurement with 2.49k bias.
    # don't want that, use 0.5v.  where's the calibration?
    clt = InputPin(sc, 'clt')
    clt.SetAnalogValue(1.0)
    sc.Add(clt)
    netA1 = pysimulavr.Net()
    netA1.Add(clt)
    netA1.Add(dev.GetPin("F1"))

    # AFR = (2.3750 * Volts) + 7.3125, so Volts = (AFR - 7.3125) / 2.3750
    # https://www.aemelectronics.com/files/instructions/30-0310%20X-Series%20Inline%20Wideband%20UEGO%20Sensor%20Controller.pdf
    o2 = InputPin(sc, 'o2')
    o2.SetAnalogValue(2.5)
    sc.Add(o2)
    netA8 = pysimulavr.Net()
    netA8.Add(o2)
    netA8.Add(dev.GetPin("K0"))

    # 12v through 3.9/1 divider => 12.7v becomes 2.6v
    bat = InputPin(sc, 'bat')
    bat.SetAnalogValue(2.6)
    sc.Add(bat)
    netA4 = pysimulavr.Net()
    netA4.Add(bat)
    #netA4.Add(dev.GetPin("F4"))
    netA4.Add(dev.GetPin("A4"))

    # outputs
    # do not need Stepping

    inj1 =  OutputPin(sc, 'inj1')
    netD8 = pysimulavr.Net()
    netD8.Add(inj1)
    netD8.Add(dev.GetPin("H5"))
    inj2 =  OutputPin(sc, 'inj2')
    netD9 = pysimulavr.Net()
    netD9.Add(inj2)
    netD9.Add(dev.GetPin("H6"))
    inj3 =  OutputPin(sc, 'inj3')
    netD10 = pysimulavr.Net()
    netD10.Add(inj3)
    netD10.Add(dev.GetPin("B4"))
    inj4 =  OutputPin(sc, 'inj4')
    netD11 = pysimulavr.Net()
    netD11.Add(inj4)
    netD11.Add(dev.GetPin("B5"))

    ign1 =  OutputPin(sc, 'ign1')
    netD40 = pysimulavr.Net()
    netD40.Add(ign1)
    netD40.Add(dev.GetPin("G1"))
    ign2 =  OutputPin(sc, 'ign2')
    netD38 = pysimulavr.Net()
    netD38.Add(ign2)
    netD38.Add(dev.GetPin("D7"))
    ign3 =  OutputPin(sc, 'ign3')
    netD52 = pysimulavr.Net()
    netD52.Add(ign3)
    netD52.Add(dev.GetPin("B1"))
    ign4 =  OutputPin(sc, 'ign4')
    netD50 = pysimulavr.Net()
    netD50.Add(ign4)
    netD50.Add(dev.GetPin("B3"))

    print "Starting AVR simulation: machine=%s speed=%d" % (proc, speed)
    print "Serial: port=%s baud=%d" % (ptyname, baud)

    configPage4 = variables.variable('configPage4')
    currentStatus = variables.variable('currentStatus')

    print "S0 uninitialized"

    printVars(variables)
    printConfig(variables)

    print "S0 write"

    writeDefaults(variables)

    print "S0 initialized"

    printConfig(variables)

    print "S0 now what's in ram"
    dumpRAM(mem, configPage4.location(), configPage4.location() + 10)
    print "S0 what's in eeprom before writing?"
    dumpEeprom(dev, EEPROM_CONFIG4_START, EEPROM_CONFIG4_START + 10)
    print "S0 write to eeprom"
    writeConfigToEeprom(variables, mem, dev)
    print "S0 done with eeprom write"
    print "S0 now what's in eeprom"
    dumpEepromHex(dev, EEPROM_CONFIG4_START, EEPROM_CONFIG4_START + 10)
    dumpEeprom(dev, EEPROM_CONFIG4_START, EEPROM_CONFIG4_START + 10)
    print "S0 done"
    print "now zero the RAM to see if loadConfig works"
    writeZeros(variables)
    print "check the zeros"
    printConfig(variables)

    printPins(variables)
    printDebugStream(rxpin2)

    for cy in range(100):
        print "================================= RUN CYCLE %d =================================" % cy 
        sc.RunTimeRange(speed)
        printDebugStream(rxpin2)
        print "time %d" % sc.GetCurrentTime()
        print "crank angle: %d crank: %s cam: %s" % (
            crank.currentAngleDegrees, tach1.state, tach2.state)
        printPins(variables)
        printStatus(variables)
        printVars(variables)
        printConfig(variables)
        #exit()

    #d.stop()

if __name__ == '__main__':
    main()
