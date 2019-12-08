#!/usr/bin/env python
# server for PW etc
# for now, block.
# eventually, we want a listener thread and a trainer thread

import os,thread, select, fcntl, termios

class Request:
    def __init__(self):
        pass

class Server:
    def __init__(self, ptyname):
        # open slave pty read/write, non-controlling
        self.sfd = os.open(ptyname, os.O_RDWR | os.O_NOCTTY)

        # non-blocking
        fcntl.fcntl(self.sfd, fcntl.F_SETFL, fcntl.fcntl(self.sfd, fcntl.F_GETFL) | os.O_NONBLOCK)

        # no-echo, non-canonical
        old = termios.tcgetattr(self.sfd)
        old[3] = old[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(self.sfd, termios.TCSADRAIN, old)

        self.epoll = select.epoll()
        self.epoll.register(self.sfd, select.EPOLLIN)

    def __del__(self):
        self.epoll.unregister(self.sfd)
        self.epoll.close()
        os.close(self.sfd)

    def run(self):
        thread.start_new_thread(self.runthread, ())

    def runthread(self):
        while True:
            events = self.epoll.poll()
            if len(events) !=  1:      # we timed out
                continue
            fileno = events[0][0]
            if self.sfd != fileno:     # should never happen; skip it if it does
                continue
            while True:
                try:
                    l = os.read(fileno, 1)
                except Exception as e: # no more to read
                    # can happen if we're just faster than the sender
                    # TODO: check for complete message
                    break
                if l is None:          # should never happen
                    break
                if len(l) == 0:        # read an empty string, shouldn't happen but does
                    break
                os.write(self.sfd, chr(ord(l) + 1))

    def calc():
        pass

def main():
    server = Server()
    server.run()

if __name__ == '__main__':
    main()
