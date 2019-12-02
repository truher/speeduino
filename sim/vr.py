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
    def __init__(self, crank, sc):
        pysimulavr.Pin.__init__(self)
        pysimulavr.PySimulationMember.__init__(self)
        self.crank = crank
        self.states = "L"
        self.state = self.states[0]
        self.sc = sc

    # overrides PySimulationMember.DoStep()
    def DoStep(self, trueHwStep):
        pos = len(self.states) * self.crank.currentAngleDegrees/720
        posFloor = int(pos)
        self.state = self.states[posFloor]
        self.SetPin(self.state)
        #self.printDebug(posFloor)
        remainingDegrees = (pos + 1 - posFloor) * 720 / len(self.states)
        remainingNs = remainingDegrees * self.crank.nsecPerDegree
        return int(remainingNs)

    def printDebug(self, posFloor):
        print "time %d VR pin %s degrees %d idx %d state %s" % (
            self.sc.GetCurrentTime(), self.name(),
            self.crank.currentAngleDegrees, posFloor, self.state)

# Simulate a 36-1 sensor for crank
class CrankVrPin(VrPin):
    def __init__(self, crank, sc):
        VrPin.__init__(self, crank, sc)
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
    def name(self):
        return "crank"

    
# Simulate a one-tooth sensor for cam
class CamVrPin(VrPin):
    def __init__(self, crank, sc):
        VrPin.__init__(self, crank, sc)
        # one tooth out of 8 positions
        #                1 2 3 4 5 6 7 8
        self.states = ("LLLLLLLLLHLLLLLL")
    def name(self):
        return "cam"
