import sys
sys.path.append("../..")
import server

import unittest
import pysimulavr
import test_client
import server
import time
import datetime

class ServerTest(unittest.TestCase):

    def testDirect(self):
        ptyname = "/tmp/testclient"
        myclient = test_client.Client(ptyname)
        myserver = server.Server(ptyname)
        myserver.run()

        result = myclient.rpc("f")
        self.assertEqual("g", result)

    def testPerf(self):
        ptyname = "/tmp/testclient"
        myclient = test_client.Client(ptyname)
        myserver = server.Server(ptyname)
        myserver.run()

        iterations = 50000
        t0 = datetime.datetime.now()
        for i in range(0,iterations):
            result = myclient.rpc("f")
            self.assertEqual("g", result) # fun fact: each assert takes ~1 us
        t1 = datetime.datetime.now()
        td = t1 - t0
        ms_per_iter = td.total_seconds() * 1000 / iterations
        print "ms per iter %f" % ms_per_iter # about 14 us per round-trip

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ServerTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
