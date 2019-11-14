#!/usr/bin/env python
#
# VR sensor pins for simulavr
#
# Copyright (C) 2019  Joel Truher (Google LLC)
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import pysimulavr, sys

# Base class
class VrPin(pysimulavr.PySimulationMember, pysimulavr.Pin):
    def __init__(self, crank):
        pysimulavr.Pin.__init__(self)
        pysimulavr.PySimulationMember.__init__(self)
        self.crank = crank
        self.states = "L"
        self.state = self.states[0]

    # overrides PySimulationMember.DoStep()
    def DoStep(self, trueHwStep):
        pos = len(self.states) * self.crank.currentAngleDegrees/720
        #sys.stdout.write("pos %f\n" % pos)
        posFloor = int(pos)
        #sys.stdout.write("posfloor %f\n" % posFloor)
        self.state = self.states[posFloor]
        self.SetPin(self.state)
        remainingDegrees = (pos + 1 - posFloor) * 720 / len(self.states)
        #sys.stdout.write("remainingDegrees %f\n" % remainingDegrees)
        remainingNs = remainingDegrees * self.crank.nsecPerDegree
        #sys.stdout.write("remainingNs %f\n" % remainingNs)
        #sys.stdout.flush()
        return int(remainingNs)

# Simulate a 36-1 sensor for crank
class CrankVrPin(VrPin):
    def __init__(self, crank):
        VrPin.__init__(self, crank)
        # 36-1, two revolutions
        #                1 2 3 4 5 6
        self.states = ("LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLL"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLH"
                       "LHLHLHLHLHLL")
#    def DoStep(self, trueHwStep):
#        VrPin.__init__(self, trueHwStep)

    
# Simulate a one-tooth sensor for cam
class CamVrPin(VrPin):
    def __init__(self, crank):
        VrPin.__init__(self, crank)
        # one tooth out of 8 positions
        #                1 2 3 4 5 6 7 8
        self.states = ("LLLLLLLLLHLLLLLL")
#    def DoStep(self, trueHwStep):
#        VrPin.__init__(self, trueHwStep)

