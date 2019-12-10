#!/usr/bin/env python
# server for PW etc
# for now, block.
# eventually, we want a listener thread and a trainer thread

import os,sys,thread, select, fcntl, termios, tty
import messages

class Server:
    def __init__(self, ptyname):
        print "init %s" % ptyname
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
        #print "run"
        thread.start_new_thread(self.runthread, ())

    def runthread(self):
        #print "runthread"
        sys.stdout.flush()
        mybuffer = ''
        while True:
            #print "poll"
            events = self.epoll.poll(1) # block here; can we block forever?
            if len(events) !=  1:       # we timed out
                continue
            fileno = events[0][0]
            if self.sfd != fileno:      # should never happen; skip it if it does
                continue
            #for mypacket in Server.readPackets(fileno, mybuffer):
            #    print "packet"
            #    self.handlePacket(mypacket)
            mybuffer = self.readPackets(fileno, mybuffer)

    # prepend and append frame markers
    def write(self, data):
        os.write(self.sfd, '\x00' + data + '\x00')

    # encoded Request => encoded Response
    def handlePacket(self, packetBytes):
        #print "handlePacket"
        if len(packetBytes) <= 2:
            print "skip short packet %d" % len(packetBytes)
            return
        req = messages.Request.fromSerial(packetBytes)
        res = messages.Response(2 * req.a, 3 * req.b)
        responseBytes = res.toSerial()
        #print "writing %s" % responseBytes.encode('hex')
        self.write(responseBytes)

    # yields packet contents with delimiters stripped
    def readPackets(self, fileno, mybuffer):
        while True:
            try:
                #print "try read"
                myread = os.read(fileno, 1000) # this should return as soon as the buffer is empty
                                               # TODO: replace this with char-at-a-time
            except Exception as e:      # no more to read
                                        # can happen if we're just faster than the sender
                print "exception %s" % str(e)
                return mybuffer
            if myread is None:          # should never happen
                print "got none"
                return mybuffer
            if len(myread) == 0:        # read an empty string, shouldn't happen but does
                print "got empty"       # seems to happen when the pipe is dead
                raise Exception("pipe seems dead")
            #print "myread %s" % myread.encode('hex')
            #print "mybuffer %s" % mybuffer.encode('hex')
            mybuffer += myread
            #print "interpret buffer %s" % mybuffer.encode('hex')
            if mybuffer[0] == '\x00':   # trim any extra zeros
                #print "starts with zero"
                if len(mybuffer) < 2:
                    #print "just one zero"
                    return mybuffer
                while mybuffer[1] == '\x00':
                    #print "trim zero"
                    mybuffer = mybuffer[0] + mybuffer[2:]
                    if len(mybuffer) == 1:
                        #print "empty buffer"
                        return mybuffer
            else:                       # skip the non-zeros and then trim the zeros
                #print "starts with non-zero"
                while mybuffer[0] != '\x00':
                    #print "trim non-zero"
                    mybuffer = mybuffer[1:]
                    if len(mybuffer) == 0:
                        return mybuffer
                while mybuffer[0] == '\x00':
                    #print "now trim zero"
                    mybuffer = mybuffer[1:]
                    if len(mybuffer) == 0:
                        return mybuffer
            # now mybuffer is aligned with a packet
            packetEnd = mybuffer.find('\x00', 1)
            if packetEnd < 0:           # no packet-end found, maybe more bytes coming
                #print "no end found"
                return mybuffer
            if packetEnd <= 2:          # weird small packet, discard it
                #print "small packet"
                mybuffer = mybuffer[packetEnd:]
                return mybuffer
            mypacket = mybuffer[1:packetEnd]
            mybuffer = mybuffer[packetEnd:]
            if len(mypacket) <= 2:      # why would this happen?
                print "wtf"
                return mybuffer
            #print "yield"
            #yield mypacket
            self.handlePacket(mypacket)
            return mybuffer


    def calc():
        pass

def main():
    server = Server("/tmp/tty3")
    server.runthread()

if __name__ == '__main__':
    main()
