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
import memory

CALIBRATION_TABLE_SIZE = 512
EEPROM_CALIBRATION_O2 = 2559
EEPROM_CALIBRATION_IAT = 3071
EEPROM_CALIBRATION_CLT = 3583
EEPROM_CONFIG2_START =  291
EEPROM_CONFIG2_END   =  419
EEPROM_CONFIG4_START =  709
EEPROM_CONFIG4_END   =  837
EEPROM_CONFIG6_START = 1127
EEPROM_CONFIG6_END   = 1255

# dumps the whole entire eeprom to the console, which verifies
# that it actually has the right thing in it, but it's hard to read :-)
def dumpEeprom(dev, start, end):
    for ost in range(start, end):
        test_str = chr(dev.eeprom.ReadFromAddress(ost))
        print "eeprom: %d: %s" % (ost, ''.join(format(ord(i), '08b') for i in test_str))
        sys.stdout.flush()

def dumpRAM(mem, start, end):
    for index in range(start, end):
        print "%d: %x" % (index - start, mem.get(index))
        sys.stdout.flush()

def dumpEepromHex(dev, start, end):
    for index in range(start, end):
        print "%d: %x" % (index - start, dev.eeprom.ReadFromAddress(index))
        sys.stdout.flush()

def writeCalibrationTablesToEeprom(eeprom, variables):
    clt = variables.variable('cltCalibrationTable')
    iat = variables.variable('iatCalibrationTable')
    o2 = variables.variable('o2CalibrationTable')
    for x in range(0, CALIBRATION_TABLE_SIZE):
        #print "write cal x: %d" % x
        #sys.stdout.flush()
        eeprom.WriteAtAddress(EEPROM_CALIBRATION_CLT + x, clt.get(x).read())
        eeprom.WriteAtAddress(EEPROM_CALIBRATION_IAT + x, iat.get(x).read())
        eeprom.WriteAtAddress(EEPROM_CALIBRATION_O2 + x, o2.get(x).read())

def writeOneConfigToEeprom(mem, eeprom, variable, start, end):
    for x in range(start, end):
        #eeprom_relative = x - start
        var_relative = variable.location() + x - start
        val = mem.get(var_relative)
        #print "addr %d val %d " % (x, val)
        eeprom.WriteAtAddress(x, val)

def writeConfigToEeprom(variables, mem, dev):
    writeOneConfigToEeprom(mem, dev.eeprom, variables.variable('configPage2'),
                           EEPROM_CONFIG2_START, EEPROM_CONFIG2_END)
    writeOneConfigToEeprom(mem, dev.eeprom, variables.variable('configPage4'),
                           EEPROM_CONFIG4_START, EEPROM_CONFIG4_END)
    writeOneConfigToEeprom(mem, dev.eeprom, variables.variable('configPage6'),
                           EEPROM_CONFIG6_START, EEPROM_CONFIG6_END)
    print "done writing config to eeprom"
    sys.stdout.flush()
    writeCalibrationTablesToEeprom(dev.eeprom, variables)
    print "done writing cal to eeprom"
    sys.stdout.flush()

    #for x in range(EEPROM_CONFIG4_START, EEPROM_CONFIG4_END):
    #    configPage4 = variables.variable('configPage4')
    #    eeprom_relative = x - EEPROM_CONFIG4_START
    #    var_relative = configPage4.location() + x - EEPROM_CONFIG4_START
    #    val = mem.get(var_relative)
    #    #print "addr %d val %d " % (x, val)
    #    dev.eeprom.WriteAtAddress(x, val)

def printPins(variables):
    print "=============== PINS ==============="
    vars = [ "pinTrigger", #19
             "pinTrigger2", #18
# what are these pins?
             "pinTPS", #A2 56 what is this?  oh it's the pin on the *board* not the chip
             "pinMAP", #A3 57
             "pinIAT", #A0 54
             "pinCLT", #A1 55
             "pinO2",  #A8 62
             "pinBat"  #A4 58
           ]
    for var in vars:
        printVarVal(variables, var)

def writeDefaults(variables):
    print "write config2"
    sys.stdout.flush()
    configPage2 = variables.variable('configPage2')
    configPage2.member('pinMapping').write(3)  # for the 0.4 shield.
    configPage2.member('mapSample').write(0)  # instantaneous
    configPage2.member('tpsMin').write(0)
    configPage2.member('tpsMax').write(255)
    configPage2.member('mapMin').write(0)
    configPage2.member('mapMax').write(255)
    #configPage2.member('pinMapping').write(41)  # for the UA4C
    configPage2.member('injLayout').write(0)  # paired
    configPage2.member('CTPSPolarity').write(0) # don't use throttle switch
    configPage2.member('CTPSEnabled').write(0) # don't use throttle switch

    print "write config4"
    sys.stdout.flush()
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
    configPage4.member('ADCFILTER_TPS').write(0)  # was 128
    configPage4.member('ADCFILTER_CLT').write(0)  # was 180
    configPage4.member('ADCFILTER_IAT').write(0)  # was 180
    configPage4.member('ADCFILTER_O2').write(0)   # was 128
    configPage4.member('ADCFILTER_BAT').write(0)  # was 128
    configPage4.member('ADCFILTER_MAP').write(0)  # was 20
    configPage4.member('ADCFILTER_BARO').write(0) # was 64

    print "write config6"
    sys.stdout.flush()
    configPage6 = variables.variable('configPage6')
    configPage6.member('egoType').write(2) # wideband

    print "write cal"
    sys.stdout.flush()
    populateCalibrationTables(variables)

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


def populateOneCalibrationTable(variables, name):
    print "write cal %s" % name
    sys.stdout.flush()
    arrayVar = variables.variable(name)
    for x in range(0, CALIBRATION_TABLE_SIZE):
        #print "write i %d v %d" % (x, x >> 1)
        arrayVar.get(x).write(x >> 1)  # TODO: use real values here

def populateCalibrationTables(variables):
    populateOneCalibrationTable(variables, 'cltCalibrationTable')
    populateOneCalibrationTable(variables, 'iatCalibrationTable')
    populateOneCalibrationTable(variables, 'o2CalibrationTable')

def printOneCalibrationTable(variables, name):
    arrayVar = variables.variable(name)
    for x in range(0, CALIBRATION_TABLE_SIZE):
        print "%20s %3d: %3d" % (name, x, arrayVar.get(x).read())

def printCalibrationTables(variables):
    printOneCalibrationTable(variables, 'cltCalibrationTable')
    printOneCalibrationTable(variables, 'iatCalibrationTable')
    printOneCalibrationTable(variables, 'o2CalibrationTable')

def printConfig(variables):
    print "========================= CONFIG2 ========================="
    sys.stdout.flush()
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
    sys.stdout.flush()
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
             'batVoltCorrect',
            ]
    for var in vars:
        printMemberVal(configPage4, var)
    print "========================= CONFIG4 ========================="
    sys.stdout.flush()
    configPage6 = variables.variable('configPage6')
    vars = [ 'egoType'
            ]
    for var in vars:
        printMemberVal(configPage6, var)
    sys.stdout.flush()

    #printCalibrationTables(variables)


def printVarVal(variables, name):
    print "%26s: %8d" % (name, variables.variable(name).read())
    sys.stdout.flush()

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
             "TPS", "VE", "VE1", "O2",
             "tpsADC",
             "CTPSActive",
             "coolant",    # +40 deg
             "cltADC",
             "iatADC",
             "IAT",
             # "batADC", # not used
             "O2ADC",
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
             # stuff about decoding
             "curGap",
             "toothCurrentCount",
             "toothLastToothTime",
             "toothLastMinusOneToothTime",
             "toothOneTime",
             "toothOneMinusOneTime",
             "targetGap",
             "validTrigger",
             "triggerFilterTime",
             # sensors
             "TPSlast",
             "TPS_time",
             "TPSlast_time",
             "MAPlast",
             "MAP_time",
             "MAPlast_time",
             "MAPcount",
             "MAPrunningValue",
             "mapErrorCount",
             # other stuff
             "fpPrimeTime", "mainLoopCount", "revolutionTime", "clutchTrigger",
             'ignitionOn', "fuelOn",
             #"iatErrorCount", # not used
             #"cltErrorCount", # not used
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

    mem = memory.SimMemory(dev)

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

    # THESE PINS ARE FOR THE 0.4 BOARD
    # https://raw.githubusercontent.com/noisymime/speeduino/master/reference/hardware/v0.4/schematic%20v0.4.3_schem.png
    # https://www.arduino.cc/en/Hacking/PinMapping2560
    # https://www.arduino.cc/en/uploads/Hacking/PinMapp2560.zip
    # TODO: add options for the NO2C and UA4C boards
    # note i think the arduino pins are what's used by speeduino (in red)
    # but the simulator knows about the AVR names only (in black)
    # a bare number x means "digital pin x" and Ax means "analog pin x"

    # serial usb not shown on schematic, it's on the arduino board.

    # RX pin, i.e. what avr thinks "TX" is
    # it adds and removes itself from the sim stepper
    # 1 = PE1
    rxpin = SerialRxPin(baud)
    netD1 = pysimulavr.Net()
    netD1.Add(rxpin)
    netD1.Add(dev.GetPin("E1"))

    # TX pin, i.e. what avr thinks "RX" is
    # it adds and removes itself from the sim stepper
    # D0 = PE0
    txpin = SerialTxPin(baud)
    netD0 = pysimulavr.Net()
    netD0.Add(txpin)
    netD0.Add(dev.GetPin("E0"))

    # Named pipe for TunerStudio
    pipe = Pipe(ptyname, speed, rxpin, txpin)
    # runs all the time
    sc.Add(pipe)

    # serial2 for debugging, also on arduino not schematic
    # (also D17 = PH0 TODO: hook up the tx pin)

    # 16 = PH1
    rxpin2 = DebugSerialRxPin(baud)
    netH1 = pysimulavr.Net()
    netH1.Add(rxpin2)
    netH1.Add(dev.GetPin("H1"))

    # it has 4096 bytes.
    print "eeprom size %d" % dev.eeprom.GetSize()
    print "DATA VERSION %d" % dev.eeprom.ReadFromAddress(0)
    # ============ simulated engine parts: ============
    # crank models engine revolutions
    crank = Crank(1000, 1)
    # runs all the time
    sc.Add(crank)
    

    # ============ inputs that work ============

    # 36-1 crank wheel
    # 19 = PD2 (all boards)
    tach1 = CrankVrPin(crank, sc)
    sc.Add(tach1)
    netD19 = pysimulavr.Net()
    netD19.Add(tach1)
    netD19.Add(dev.GetPin("D2"))

    # 1-tooth cam wheel
    # TODO: implement sec trigger wheel correctly in speeduino
    # 18 = PD3 (all boards)
    tach2 = CamVrPin(crank, sc)
    sc.Add(tach2)
    netD18 = pysimulavr.Net()
    netD18.Add(tach2)
    netD18.Add(dev.GetPin("D3"))

    # ============ inputs that don't yet work ============

    # 12v through 3.9/1 divider => 12.7v becomes 2.6v
    # A2 = PF2 (ua4c)
    # A4 = PF4 (0.4)
    bat = InputPin(sc, 'bat')
    bat.SetAnalogValue(2.6)
    sc.Add(bat)
    netA4 = pysimulavr.Net()
    netA4.Add(bat)
    netA4.Add(dev.GetPin("F4"))
    #netA4.Add(dev.GetPin("A4"))

    # i think tps is just linear, 0-5 = 0-100, but i'm not sure.
    # A3 = PF3 (ua4c)
    # A2 = PF2 (0.4)
    # pin set to A2 and is actually 56
    tps = InputPin(sc, 'tps')
    #tps.SetAnalogValue(0.1)
    sc.Add(tps)
    netA2 = pysimulavr.Net()
    netA2.Add(tps)
    netA2.Add(dev.GetPin("F2"))
    #netA2.Add(dev.GetPin("A2"))

    # the map transfer function is.
    # Vout = 5.1 * (0.00369*P + 0.04)
    # https://www.mouser.com/datasheet/2/302/MPX4250-1127330.pdf
    # A0 = PF0 (ua4c)
    # A3 = PF3  (0.4)
    mapPin = InputPin(sc, 'map')
    mapPin.SetAnalogValue(1.0)
    sc.Add(mapPin)
    netA3 = pysimulavr.Net()
    netA3.Add(mapPin)
    netA3.Add(dev.GetPin("F3"))
    #netA3.Add(dev.GetPin("A3"))

    # iat is a resistance measurement with 2.49k bias.
    # don't want that, use 0-5v.  where's the calibration?
    # A5 = PF5 (ua4c)
    # A0 = PF0 (0.4) == "56" on the board
    iat = InputPin(sc, 'iat')
    iat.SetAnalogValue(1.0)
    sc.Add(iat)
    netA0 = pysimulavr.Net()
    netA0.Add(iat)
    netA0.Add(dev.GetPin("F0"))
    #netA0.Add(dev.GetPin("A0"))

    # clt is a resistance measurement with 2.49k bias.
    # don't want that, use 0.5v.  where's the calibration?
    # A4 = PF4 (ua4c)
    # A1 = PF1 (0.4)
    clt = InputPin(sc, 'clt')
    clt.SetAnalogValue(1.0)
    sc.Add(clt)
    netA1 = pysimulavr.Net()
    netA1.Add(clt)
    netA1.Add(dev.GetPin("F1"))
    #netA1.Add(dev.GetPin("A1"))

    # AFR = (2.3750 * Volts) + 7.3125, so Volts = (AFR - 7.3125) / 2.3750
    # https://www.aemelectronics.com/files/instructions/30-0310%20X-Series%20Inline%20Wideband%20UEGO%20Sensor%20Controller.pdf
    # A1 = PF1 (ua4c)
    # A8 = PK0 (0.4)
    o2 = InputPin(sc, 'o2')
    o2.SetAnalogValue(2.5)
    sc.Add(o2)
    netA8 = pysimulavr.Net()
    netA8.Add(o2)
    netA8.Add(dev.GetPin("K0"))
    #netA8.Add(dev.GetPin("A8"))

    # outputs
    # do not need Stepping

    # 8 = PH5 (ua4c)
    # 8 = PH5 (0.4)
    inj1 =  OutputPin(sc, 'inj1')
    netD8 = pysimulavr.Net()
    netD8.Add(inj1)
    netD8.Add(dev.GetPin("H5"))

    # 7 = PH4 (ua4c)
    # 9 = PH6 (0.4)
    inj2 =  OutputPin(sc, 'inj2')
    netD9 = pysimulavr.Net()
    netD9.Add(inj2)
    netD9.Add(dev.GetPin("H6"))

    # 6 = PH3 (ua4c)
    # 10 = PB4 (0.4)
    inj3 =  OutputPin(sc, 'inj3')
    netD10 = pysimulavr.Net()
    netD10.Add(inj3)
    netD10.Add(dev.GetPin("B4"))

    # 5 = PE3 (ua4c)
    # 11 = PB5 (0.4)
    inj4 =  OutputPin(sc, 'inj4')
    netD11 = pysimulavr.Net()
    netD11.Add(inj4)
    netD11.Add(dev.GetPin("B5"))

    # 35 = PC2 (ua4c)
    # 40 = PG1 (0.4)
    ign1 =  OutputPin(sc, 'ign1')
    netD40 = pysimulavr.Net()
    netD40.Add(ign1)
    netD40.Add(dev.GetPin("G1"))

    # 36 = PC1 (ua4c)
    # 38 = PD7 (0.4)
    ign2 =  OutputPin(sc, 'ign2')
    netD38 = pysimulavr.Net()
    netD38.Add(ign2)
    netD38.Add(dev.GetPin("D7"))

    # 33 = PC4 (ua4c)
    # 52 = PB1 (0.4)
    ign3 =  OutputPin(sc, 'ign3')
    netD52 = pysimulavr.Net()
    netD52.Add(ign3)
    netD52.Add(dev.GetPin("B1"))

    # 34 = PC3 (ua4c)
    # 50 = PB3 (0.4)
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
    print "S0 printconfig"
    sys.stdout.flush()
    printConfig(variables)
    sys.stdout.flush()

    print "S0 write"
    sys.stdout.flush()

    writeDefaults(variables)

    print "S0 initialized"

    printConfig(variables)
    sys.stdout.flush()

    print "S0 now what's in ram"
    sys.stdout.flush()
    dumpRAM(mem, configPage4.location(), configPage4.location() + 10)
    print "S0 what's in eeprom before writing?"
    sys.stdout.flush()
    dumpEeprom(dev, EEPROM_CONFIG4_START, EEPROM_CONFIG4_START + 10)
    print "S0 write to eeprom"
    sys.stdout.flush()
    writeConfigToEeprom(variables, mem, dev)
    sys.stdout.flush()
    print "S0 done with eeprom write"
    print "S0 now what's in eeprom"
    sys.stdout.flush()
    dumpEepromHex(dev, EEPROM_CONFIG4_START, EEPROM_CONFIG4_START + 10)
    dumpEeprom(dev, EEPROM_CONFIG4_START, EEPROM_CONFIG4_START + 10)
    print "S0 done"
    print "now zero the RAM to see if loadConfig works"
    sys.stdout.flush()
    writeZeros(variables)
    print "check the zeros"
    sys.stdout.flush()
    printConfig(variables)
    sys.stdout.flush()

    printPins(variables)
    sys.stdout.flush()
    printDebugStream(rxpin2)
    sys.stdout.flush()

    for cy in range(100):
        print "================================= RUN CYCLE %d =================================" % cy 

        # try setting stuff here?

        # tps is read at 15hz or 32 loops
        #tpsval = (cy * 0.1) % 5
        #print "tpsval %f" % tpsval
        #tps.SetAnalogValue(tpsval)

        # clt/iat/o2/bat are read at 4hz

        sc.RunTimeRange(speed*1000)
        printDebugStream(rxpin2)
        print "time %f" % (sc.GetCurrentTime() / 10**9)  # ns -> sec
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
