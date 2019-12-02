#!/usr/bin/env python
#
# Output pins for simulavr
#
# Copyright (C) 2019  Joel Truher (Google LLC)
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import pysimulavr

class OutputPin(pysimulavr.Pin):
    def __init__(self, sc, name):
        pysimulavr.Pin.__init__(self)
        #self.pos = -1
        self.name = name
        self.sc = sc

    # overrides Pin.SetInState()
    def SetInState(self, pin):
        pysimulavr.Pin.SetInState(self, pin)
        self.state = pin.outState
        #print "time %d output %s state %s" % (self.sc.GetCurrentTime(), self.name, self.state)
