import ctypes

# represents the memory of the device
class Memory():
    def get(self,addr):      # int
        raise NotImplementedError()
    def set(self,addr,val):  # int
        raise NotImplementedError()

# internal python, for testing and maybe page flipping?
# the cpp equivalent has another wrapper (one per byte) with a hook for tracing
# and it pre-initializes the whole range
class DictMemory(Memory):
    def __init__(self):
        self.rw = {}
    def get(self, addr):      # int
        if addr not in self.rw:
            return 0
        return self.rw[addr]
    def set(self, addr, val): # int
        if not isinstance(val, int):
            raise ValueError("wrong value type: %s " % type(val))
        self.rw[addr] = val

# interface to pysimulavr memory api
class SimMemory(Memory):
    def __init__(self, dev):
        self.dev = dev
    def get(self, addr):
        if addr < 0 or addr > 8703: # mega2560 has 8k of ram
            raise ValueError("addr out of bounds: %d" % addr)
        #print "get addr %d" % addr
        val = self.dev.GetRWMem(addr)
        #print "got addr %d val %d" % (addr, val)
        if not isinstance(val, int):
            raise ValueError("wrong value type: %s " % type(val))
        return val
    def set(self, addr, val):
        if addr < 0 or addr > 8703: # mega2560 has 8k of ram
            raise ValueError("addr out of bounds: %d" % addr)
        if not isinstance(val, int):
            raise ValueError("wrong value type: %s " % type(val))
        #print "set addr %d val %d" % (addr, val)
        #self.dev.setRWMem(addr, val)
        #val = ctypes.c_ubyte(ord(val)).value
        val = ctypes.c_ubyte(val).value
        self.dev.SetRWMem(addr, val)
