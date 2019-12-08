#!/usr/bin/env python

import sys, os, pty, select, fcntl, termios

# simple client for python server
class Client:
    def __init__(self, ptyname):
        self.ptyname = ptyname
        self.mfd = self.makePty()
        self.epoll = select.epoll()
        self.epoll.register(self.mfd, select.EPOLLIN)

    def __del__(self):
        self.epoll.unregister(self.mfd)
        self.epoll.close()
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
        old[3] = old[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(mfd, termios.TCSADRAIN, old)
        return mfd

    def rpc(self, request):
        os.write(self.mfd, request)
        while True:                         # wait for input; TODO: check for complete message
            events = self.epoll.poll()
            if len(events) != 1: continue   # timed out
            fileno = events[0][0]
            if self.mfd != fileno: continue # should never happen
            while True:                     # read until exhausted
                try:
                    l = os.read(fileno, 1)
                except Exception as e: break
                if l is None: break
                if len(l) == 0: break
                return l                    # for now it's just one char
