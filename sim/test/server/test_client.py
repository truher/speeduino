import sys
sys.path.append("../..")
import server

import sys, os, pty, select, fcntl, termios, tty
import collections

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
        tty.setraw(mfd)
        return mfd

    def write(self, data):
        os.write(self.mfd, '\x00' + data + '\x00')

    def rpc(self, request):
        self.write(request)
        mybuffer = ''
        while True:                         # wait for input
            events = self.epoll.poll(1)
            if len(events) != 1: continue   # timed out
            fileno = events[0][0]
            if self.mfd != fileno: continue # should never happen
            packetGen = server.Server.readPackets(fileno, mybuffer)
            # take the first one, maybe it's the right one?
            # TODO: find the actual right one?  maybe catching up is enough
            mypacket = next(packetGen)
            # empty the queue, to try to catch up if we're behind
            collections.deque(packetGen, maxlen=0)
            return mypacket
