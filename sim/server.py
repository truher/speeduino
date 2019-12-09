#!/usr/bin/env python
# server for PW etc
# for now, block.
# eventually, we want a listener thread and a trainer thread

import os,thread, select, fcntl, termios, tty
import messages

class Request:
    def __init__(self):
        pass

class Server:
    def __init__(self, ptyname):
        # open slave pty read/write, non-controlling
        self.sfd = os.open(ptyname, os.O_RDWR | os.O_NOCTTY)
        # non-blocking
        fcntl.fcntl(self.sfd, fcntl.F_SETFL, fcntl.fcntl(self.sfd, fcntl.F_GETFL) | os.O_NONBLOCK)
        # this sets a combination of flags
        tty.setraw(self.sfd)
        self.epoll = select.epoll()
        self.epoll.register(self.sfd, select.EPOLLIN)

    def __del__(self):
        self.epoll.unregister(self.sfd)
        self.epoll.close()
        os.close(self.sfd)

    def run(self):
        thread.start_new_thread(self.runthread, ())

    def runthread(self):
        mybuffer = ''
        while True:
            events = self.epoll.poll(1) # block here; can we block forever?
            if len(events) !=  1:       # we timed out
                continue
            fileno = events[0][0]
            if self.sfd != fileno:      # should never happen; skip it if it does
                continue
            for mypacket in Server.readPackets(fileno, mybuffer):
                if len(mypacket) <= 2:
                    print "skip short packet %d" % len(mypacket)
                    continue
                res = self.handlePacket(mypacket)
                self.write(res)

    # prepend and append frame markers
    def write(self, data):
        os.write(self.sfd, '\x00' + data + '\x00')

    # encoded Request => encoded Response
    def handlePacket(self, packetBytes):
        req = messages.Request.fromSerial(packetBytes)
        res = messages.Response(2 * req.a, 3 * req.b)
        return res.toSerial()

    # yields packet contents with delimiters stripped
    @staticmethod
    def readPackets(fileno, mybuffer):
        while True:
            try:
                myread = os.read(fileno, 1000) # this should return as soon as the buffer is empty
            except Exception as e:      # no more to read
                                        # can happen if we're just faster than the sender
                return
            if myread is None:          # should never happen
                return
            if len(myread) == 0:        # read an empty string, shouldn't happen but does
                return
            mybuffer += myread
            if mybuffer[0] == '\x00':   # trim the zeros
                while mybuffer[0] == '\x00':
                    mybuffer = mybuffer[1:]
                    if len(mybuffer) == 0:
                        return
            else:                       # skip the non-zeros and then trim the zeros
                while mybuffer[0] != '\x00':
                    mybuffer = mybuffer[1:]
                    if len(mybuffer) == 0:
                        return
                while mybuffer[0] == '\x00':
                    mybuffer = mybuffer[1:]
                    if len(mybuffer) == 0:
                        return
            # now mybuffer is aligned with a packet
            packetEnd = mybuffer.find('\x00')
            if packetEnd < 0:           # no packet-end found, maybe more bytes coming
                return
            if packetEnd <= 2:          # weird small packet, discard it
                mybuffer = mybuffer[packetEnd:]
                return
            mypacket = mybuffer[:packetEnd]
            mybuffer = mybuffer[packetEnd:]
            if len(mypacket) <= 2:      # why would this happen?
                return
            yield mypacket


    def calc():
        pass

def main():
    server = Server()
    server.run()

if __name__ == '__main__':
    main()
