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
        cur = self.GetAnalogValue(5.0)
        cur += 0.1 * random.random() - 0.05
        #print(cur)
        # random walk
        self.SetAnalogValue(cur)
        print "time %d input %s input %f" % (self.sc.GetCurrentTime(), self.name, cur)
        return 1000000  # 1 ms
        #return 10**9
