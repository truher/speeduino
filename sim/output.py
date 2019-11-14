#!/usr/bin/env python
#
# Output pins for simulavr
#
# Copyright (C) 2015  Kevin O'Connor
# Modified 2019 Joel Truher
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import pysimulavr

class OutputPin(pysimulavr.Pin):
    def __init__(self):
        pysimulavr.Pin.__init__(self)
        self.pos = -1

    # overrides Pin.SetInState()
    def SetInState(self, pin):
        pysimulavr.Pin.SetInState(self, pin)
        self.state = pin.outState
