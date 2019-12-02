import sys
sys.path.append("../..")
import dwarf
import memory

import unittest
import pysimulavr

class XPin(pysimulavr.Pin):
  
  def __init__(self, dev, name, state = None):
    pysimulavr.Pin.__init__(self)
    self.dev=dev
    self.name = name
    devpin = dev.GetPin(name)
    if state is not None: self.SetPin(state)
    self.__net = pysimulavr.Net()
    self.__net.Add(self)
    self.__net.Add(devpin)

class PinsTest(unittest.TestCase):

    def testTrue(self):
        self.assertTrue(True)

    # verifies correct simulation of ADC
    def testSim(self):
        sc = pysimulavr.SystemClock.Instance()
        sc.ResetClock()
        pysimulavr.DumpManager.Instance().Reset()
        pysimulavr.DumpManager.Instance().SetSingleDeviceApp()
        dev = pysimulavr.AvrFactory.instance().makeDevice("atmega2560")
        filename = 'pins.elf'
        dev.Load(filename)
        dev.SetClockFreq(62)  # clock period in ns (16 MHz)
        sc.Add(dev)


        pins = [XPin(dev, "F0", 'a'),
                XPin(dev, "F1", 'a'),
                XPin(dev, "F2", 'a'),
                XPin(dev, "F3", 'a'),
                XPin(dev, "F4", 'a'),
                XPin(dev, "F5", 'a'),
                XPin(dev, "F6", 'a'),
                XPin(dev, "F7", 'a'),
                XPin(dev, "K0", 'a'),
                XPin(dev, "K1", 'a'),
                XPin(dev, "K2", 'a'),
                XPin(dev, "K3", 'a'),
                XPin(dev, "K4", 'a'),
                XPin(dev, "K5", 'a'),
                XPin(dev, "K6", 'a'),
                XPin(dev, "K7", 'a')]

        for num, pin in enumerate(pins):
            pin.SetAnalogValue(5.0 * (num + 1) / 100)

        sc.RunTimeRange(10000000) # enough time to do lots of ADC

        variables = dwarf.Globals(memory.SimMemory(dev), filename, 'src/pins.ino.cpp')
        val = variables.variable("val")
        for num, pin in enumerate(pins):
            self.assertAlmostEqual(1024 * (num + 1) / 100, val.get(num).read())

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(PinsTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
