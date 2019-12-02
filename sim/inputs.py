#!/usr/bin/env python
#
# Analog input pins for simulavr
#
# Copyright (C) 2019  Joel Truher (Google LLC)
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import pysimulavr, random

class InputPin(pysimulavr.PySimulationMember, pysimulavr.Pin):
    def __init__(self, sc, name):
        pysimulavr.Pin.__init__(self)
        pysimulavr.PySimulationMember.__init__(self)
        self.SetPin('a')  # ?
        self.sc = sc
        self.name = name

    def DoStep(self, trueHwStep):
        cur = self.GetAnalogValue(5.0) # supplying vcc here is lame
        # random walk
        cur += 0.1 * random.random() - 0.05
        #cur = 4.0 * random.random() + 0.5
        #cur = (cur + 0.1) % 5.0
        #print(cur)
        self.SetAnalogValue(cur)
        #print "time %d input %s input %f" % (self.sc.GetCurrentTime(), self.name, cur)
        return 10000000  # 10 ms
        #return 10**9
