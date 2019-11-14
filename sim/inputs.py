#!/usr/bin/env python
#
# Analog input pins for simulavr
#
# Copyright (C) 2015  Kevin O'Connor
# Modified 2019 Joel Truher
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import pysimulavr

class InputPin(pysimulavr.PySimulationMember, pysimulavr.Pin):
    def __init__(self):
        pysimulavr.Pin.__init__(self)
        pysimulavr.PySimulationMember.__init__(self)
        self.SetPin('a')  # ?

    def DoStep(self, trueHwStep):
        return 10**9
