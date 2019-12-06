#!/usr/bin/env python
#
# Named pipe for simulavr
#
# Copyright (C) 2019  Joel Truher (Google LLC)
# Copyright (C) 2015  Kevin O'Connor
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import sys, os, pty, select, fcntl, termios
import pysimulavr
import binascii
import datetime


class Pipe(pysimulavr.PySimulationMember):
    def __init__(self, port, speed, rxpin, txpin):
        pysimulavr.PySimulationMember.__init__(self)
        self.ptyname = port
        self.fd = self.makePty()
        self.delay = speed/1000
        self.txpin = txpin
        self.rxpin = rxpin
        self.dumpfile = open('pipe.dump', 'wb')
        self.dumpfile.write("START PIPE DUMP\n")
        self.dumpfile.flush()

    def __del__(self):
        os.unlink(self.ptyname)

    def makePty(self):
        mfd, sfd = pty.openpty()
        try:
            os.unlink(self.ptyname)
        except os.error:
            pass
        os.symlink(os.ttyname(sfd), self.ptyname)
        fcntl.fcntl(mfd, fcntl.F_SETFL, fcntl.fcntl(mfd, fcntl.F_GETFL) | os.O_NONBLOCK)
        old = termios.tcgetattr(mfd)
        old[3] = old[3] & ~termios.ECHO
        termios.tcsetattr(mfd, termios.TCSADRAIN, old)
        return mfd

    # overrides PySimulationMember.DoStep()
    def DoStep(self, trueHwStep):
        # pipe "rx" is avr "tx"
        d = self.rxpin.popChars()
        if d:
            #sys.stdout.write(d)
            #sys.stdout.flush()
            os.write(self.fd, d)
            self.dumpfile.write("RX %s %s\n" % (str(datetime.datetime.now()), binascii.hexlify(d)))
            self.dumpfile.flush()

        # pipe "tx" is avr "rx"
        res = select.select([self.fd], [], [], 0)
        if res[0]:
            d = os.read(self.fd, 1024)
            #sys.stdout.write(binascii.hexlify(d))
            #sys.stdout.write(' ')
            #sys.stdout.flush()
            self.txpin.pushChars(d)
            self.dumpfile.write("TX %s %s\n" % (str(datetime.datetime.now()), binascii.hexlify(d)))
            self.dumpfile.flush()
        return self.delay
