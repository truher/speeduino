#!/usr/bin/env python
#
# Crank angle for simulavr
#
# Copyright (C) 2015  Kevin O'Connor
# Modified 2019 Joel Truher
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import pysimulavr, sys

# TODO: support for starting, i.e. not a fixed RPM
class Crank(pysimulavr.PySimulationMember):
    def __init__(self, rpm, degreesPerStep):
        pysimulavr.PySimulationMember.__init__(self)
        self.currentAngleDegrees = 0   # 0-720
        self.degreesPerStep = degreesPerStep
        self.SetRPM(rpm)

    # overrides PySimulationMember.DoStep()
    def DoStep(self, trueHwStep):
        self.currentAngleDegrees = (self.currentAngleDegrees + self.degreesPerStep) % 720
        #sys.stdout.write("currentAngleDegrees %f\n" % self.currentAngleDegrees)
        return self.nsecPerStep

    def SetRPM(self, rpm):
        self.rpm = rpm
        self.secPerRev = 60.0 / self.rpm
        self.secPerDegree = self.secPerRev / 360.0
        #sys.stdout.write("secPerDegree %f\n" % self.secPerDegree)
        self.nsecPerDegree = self.secPerDegree * 10**9
        #sys.stdout.write("nsecPerDegree %f\n" % self.nsecPerDegree)
        self.nsecPerStep = int(self.nsecPerDegree * self.degreesPerStep)
        #sys.stdout.write("nsecPerStep %f\n" % self.nsecPerStep)
        #sys.stdout.write("degreesPerStep %f\n" % self.degreesPerStep)
        #sys.stdout.flush()
