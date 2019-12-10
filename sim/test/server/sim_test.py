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
import thread

def main():

    filename = 'client_app.elf'
    cu_name = 'src/client_app.ino.cpp'
    proc = "atmega2560"
    speed = 16000000
    sc = pysimulavr.SystemClock.Instance()
    sc.ResetClock()
    pysimulavr.DumpManager.Instance().Reset()
    pysimulavr.DumpManager.Instance().SetSingleDeviceApp()

    hwusart_factory = pysimulavr.HWUsartFactory('/tmp/tty')
    dev = pysimulavr.AvrDevice_atmega2560(hwusart_factory)

    #dev = pysimulavr.AvrFactory.instance().makeDevice(proc)
    dev.Load(filename)
    dev.SetClockFreq(10**9 / speed)
    sc.Add(dev)
    sc.RunTimeRange(5 * 10**8) # run 0.5 (simulated) seconds

#    myserver = server.Server("/tmp/tty3")

#    myserver.run()
    sc.RunTimeRange(10 * 10**9) # run ten (simulated) seconds

#    thread.start_new_thread(sc.RunTimeRange, (10 * 10**9,))
#    myserver.runthread()

if __name__ == '__main__':
    main()
