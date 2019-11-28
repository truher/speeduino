import unittest
import dwarf
import pysimulavr
import ctypes

class SimMemory(dwarf.Memory):
    def __init__(self, dev):
        self.dev = dev
    def get(self, addr):
        foo = self.dev.GetRWMem(addr)
        val = self.dev.GetRWMem(addr)
        if not isinstance(val, int):
            raise ValueError("wrong value type: %s " % type(val))
        return val
    def set(self, addr, val):
        if not isinstance(val, int):
            raise ValueError("wrong value type: %s " % type(val))
        val = ctypes.c_ubyte(ord(val)).value
        self.dev.SetRWMem(addr, val)

class TypesTest(unittest.TestCase):

    def testTrue(self):
        self.assertTrue(True)

    def testNonExistent(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem,
            'test/types.elf',
            'test/types.ino.cpp')
        with self.assertRaises(ValueError):
            variables.variable("nonexistent variable")

    def checkPrimitiveWriteReadback(self, variables, varname, encoding, size, location, value):
        v = variables.variable(varname)
        self.assertEqual('Primitive', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        self.assertEqual(encoding, v.encoding())
        self.assertEqual(size, v.byte_size())
        self.assertEqual(location, v.location())   
        v.write(value)
        self.assertEqual(value, v.read())

    def checkPrimitiveRead(self, variables, varname, encoding, size, location, value, approx=False):
        v = variables.variable(varname)
        self.assertEqual('Primitive', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        self.assertEqual(encoding, v.encoding())
        self.assertEqual(size, v.byte_size())
        self.assertEqual(location, v.location())   
        if approx: # for floats
            self.assertAlmostEqual(value, v.read(), 2)
        else:
            self.assertEqual(value, v.read())

    def checkArrayWriteReadback(self, variables, varname, upper_bound, encoding, size, location0, location1, value0, value1):
        v = variables.variable(varname)
        self.assertEqual('Array', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        self.assertEqual(upper_bound, v.upper_bound())
        e0 = v.get(0)
        self.assertEqual('Primitive', e0.__class__.__name__)
        self.assertEqual('DW_TAG_variable', e0.var_die.tag)
        self.assertEqual(encoding, e0.encoding())
        self.assertEqual(size, e0.byte_size())
        self.assertEqual(location0, e0.location())   
        e1 = v.get(1)
        self.assertEqual(encoding, e1.encoding())
        self.assertEqual(size, e1.byte_size())
        self.assertEqual(location1, e1.location())   
        e0.write(value0)
        e1.write(value1)
        self.assertEqual(value0, e0.read())
        self.assertEqual(value1, e1.read())

    def checkArrayRead(self, variables, varname, upper_bound, encoding, size, location0, location1, value0, value1, approx=False):
        v = variables.variable(varname)
        self.assertEqual('Array', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        self.assertEqual(upper_bound, v.upper_bound())
        e0 = v.get(0)
        self.assertEqual('Primitive', e0.__class__.__name__)
        self.assertEqual('DW_TAG_variable', e0.var_die.tag)
        self.assertEqual(encoding, e0.encoding())
        self.assertEqual(size, e0.byte_size())
        self.assertEqual(location0, e0.location())   
        e1 = v.get(1)
        self.assertEqual(encoding, e1.encoding())
        self.assertEqual(size, e1.byte_size())
        self.assertEqual(location1, e1.location())   
        if approx:
            self.assertAlmostEqual(value0, e0.read(), 2)
            self.assertAlmostEqual(value1, e1.read(), 2)
        else:
            self.assertEqual(value0, e0.read())
            self.assertEqual(value1, e1.read())

    def checkStructWriteReadback(self, variables, varname, membername, encoding, size, location, value, bit_size=None, bit_offset=None):
        v = variables.variable(varname)
        self.assertEqual('Struct', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        e0 = v.member(membername)
        self.assertEqual('Primitive', e0.__class__.__name__)
        self.assertEqual('DW_TAG_member', e0.var_die.tag)
        self.assertEqual(encoding, e0.encoding())
        self.assertEqual(size, e0.byte_size())
        self.assertEqual(location, e0.location())   
        if bit_size is not None:
            self.assertEqual(bit_size, e0.bit_size())
        if bit_offset is not None:
            self.assertEqual(bit_offset, e0.bit_offset())
        e0.write(value)
        self.assertEqual(value, e0.read())

    def checkStructRead(self, variables, varname, membername, encoding, size, location, value, approx=False, bit_size=None, bit_offset=None):
        v = variables.variable(varname)
        self.assertEqual('Struct', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        e0 = v.member(membername)
        self.assertEqual('Primitive', e0.__class__.__name__)
        self.assertEqual('DW_TAG_member', e0.var_die.tag)
        self.assertEqual(encoding, e0.encoding())
        self.assertEqual(size, e0.byte_size())
        self.assertEqual(location, e0.location())   
        if bit_size is not None:
            self.assertEqual(bit_size, e0.bit_size())
        if bit_offset is not None:
            self.assertEqual(bit_offset, e0.bit_offset())
        if approx:
            self.assertAlmostEqual(value, e0.read(), 2)
        else:
            self.assertEqual(value, e0.read())

    # check initial values without running the code
    def testDwarf(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem,
            'test/types.elf',
            'test/types.ino.cpp')

        self.checkPrimitiveWriteReadback(variables, 'v1', 2, 1, 648, True) # bool => bool
        self.checkPrimitiveWriteReadback(variables, 'v2', 2, 1, 647, True) # bool => bool
        self.checkPrimitiveWriteReadback(variables, 'v3', 8, 1, 646, 3) # uchar => int
        self.checkPrimitiveWriteReadback(variables, 'v4', 6, 1, 645, 4) # char => int
        self.checkPrimitiveWriteReadback(variables, 'v5', 4, 4, 641, 5.5) # float(aka double) => float
        self.checkPrimitiveWriteReadback(variables, 'v6', 4, 4, 637, 6.5) # float => float
        self.checkPrimitiveWriteReadback(variables, 'v7', 5, 2, 635, 7) # short(aka int) => short
        self.checkPrimitiveWriteReadback(variables, 'v8', 5, 4, 631, 8) # long(aka int) => int
        self.checkPrimitiveWriteReadback(variables, 'v9', 5, 2, 629, 9) # short => short
        self.checkPrimitiveWriteReadback(variables, 'v10', 7, 2, 627, 10) # size_t(uint16) => short
        self.checkPrimitiveWriteReadback(variables, 'v11', 8, 1, 626, 11) # uchar => short
        self.checkPrimitiveWriteReadback(variables, 'v12', 7, 2, 624, 12) # uint(16) => short
        self.checkPrimitiveWriteReadback(variables, 'v13', 7, 4, 620, 13) # uint(32) => int
        self.checkPrimitiveWriteReadback(variables, 'v14', 7, 2, 618, 14) # uint(16) => int

        self.checkArrayWriteReadback(variables, 'av1', 1, 2, 1, 578, 579, True, True)
        self.checkArrayWriteReadback(variables, 'av2', 1, 2, 1, 576, 577, True, True)
        self.checkArrayWriteReadback(variables, 'av3', 1, 8, 1, 574, 575, 3, 23)
        self.checkArrayWriteReadback(variables, 'av4', 1, 6, 1, 572, 573, 4, 24)
        self.checkArrayWriteReadback(variables, 'av5', 1, 4, 4, 564, 568, 5.5, 25.5)
        self.checkArrayWriteReadback(variables, 'av6', 1, 4, 4, 556, 560, 6.5, 26.5)
        self.checkArrayWriteReadback(variables, 'av7', 1, 5, 2, 552, 554, 7, 27)
        self.checkArrayWriteReadback(variables, 'av8', 1, 5, 4, 544, 548, 8, 28)
        self.checkArrayWriteReadback(variables, 'av9', 1, 5, 2, 540, 542, 9, 29)
        self.checkArrayWriteReadback(variables, 'av10', 1, 7, 2, 536, 538, 10, 30)
        self.checkArrayWriteReadback(variables, 'av11', 1, 8, 1, 534, 535, 11, 31)
        self.checkArrayWriteReadback(variables, 'av12', 1, 7, 2, 530, 532, 12, 32)
        self.checkArrayWriteReadback(variables, 'av13', 1, 7, 4, 522, 526, 13, 33)
        self.checkArrayWriteReadback(variables, 'av14', 1, 7, 2, 518, 520, 14, 34)

        self.checkStructWriteReadback(variables, 'sv1', 's1v1', 2, 1, 584, True)
        self.checkStructWriteReadback(variables, 'sv1', 's1v2', 2, 1, 585, True)
        self.checkStructWriteReadback(variables, 'sv1', 's1v3', 8, 1, 586, 3)
        self.checkStructWriteReadback(variables, 'sv1', 's1v4', 6, 1, 587, 4)
        self.checkStructWriteReadback(variables, 'sv1', 's1v5', 4, 4, 588, 5.5)
        self.checkStructWriteReadback(variables, 'sv1', 's1v6', 4, 4, 592, 6.5)
        self.checkStructWriteReadback(variables, 'sv1', 's1v7', 5, 2, 596, 7)
        self.checkStructWriteReadback(variables, 'sv1', 's1v8', 5, 4, 598, 8)
        self.checkStructWriteReadback(variables, 'sv1', 's1v9', 5, 2, 602, 9)
        self.checkStructWriteReadback(variables, 'sv1', 's1v10', 7, 2, 604, 10)
        self.checkStructWriteReadback(variables, 'sv1', 's1v11', 8, 1, 606, 11)
        self.checkStructWriteReadback(variables, 'sv1', 's1v12', 7, 2, 607, 12)
        self.checkStructWriteReadback(variables, 'sv1', 's1v13', 7, 4, 609, 13)
        self.checkStructWriteReadback(variables, 'sv1', 's1v14', 7, 2, 613, 14)
        self.checkStructWriteReadback(variables, 'sv1', 's1v15', 8, 1, 615, 15, 4, 4)
        self.checkStructWriteReadback(variables, 'sv1', 's1v16', 8, 1, 615, 4, 4, 0)
        self.checkStructWriteReadback(variables, 'sv1', 's1v17', 8, 1, 616, 3, 4, 4)
        self.checkStructWriteReadback(variables, 'sv1', 's1v18', 8, 1, 616, 1, 1, 3)
        self.checkStructWriteReadback(variables, 'sv1', 's1v19', 8, 1, 616, 3, 3, 0)
        self.checkStructWriteReadback(variables, 'sv1', 's1v20', 8, 1, 617, 3, 2, 6)
        self.checkStructWriteReadback(variables, 'sv1', 's1v21', 8, 1, 617, 3, 2, 4)
        self.checkStructWriteReadback(variables, 'sv1', 's1v22', 8, 1, 617, 3, 2, 2)

        # TODO: make the pointers work

        # vv0 = variables.variable('vv0')
        # self.assertEqual(34, vv0.get(0).read())
        # vv1 = variables.variable('vv1')
        # self.assertEqual('\x10', vv1.get(0).read())

        # verify using raw access
        self.assertEqual(int('0x18',16), mem.get(573))  # av4[1] (24 dec)
        self.assertEqual(int('0x04',16), mem.get(572))  # av4[0]
        self.assertEqual(int('0x41',16), mem.get(571))  # av5[1] lsb
        self.assertEqual(int('0xcc',16), mem.get(570))  #
        self.assertEqual(int('0x00',16), mem.get(569))  #
        self.assertEqual(int('0x00',16), mem.get(568))  # av5[1] msb
        self.assertEqual(int('0x40',16), mem.get(567))  # av5[0] lsb
        self.assertEqual(int('0xb0',16), mem.get(566))  # 
        self.assertEqual(int('0x00',16), mem.get(565))  # 
        self.assertEqual(int('0x00',16), mem.get(564))  # av5[0] msb
        self.assertEqual(int('0x41',16), mem.get(563))  # av6[1] lsb
        self.assertEqual(int('0xd4',16), mem.get(562))  # 
        self.assertEqual(int('0x00',16), mem.get(561))  #
        self.assertEqual(int('0x00',16), mem.get(560))  # av6[1] msb
        self.assertEqual(int('0x40',16), mem.get(559))  # av6[0] lsb
        self.assertEqual(int('0xd0',16), mem.get(558))  #
        self.assertEqual(int('0x00',16), mem.get(557))  #
        self.assertEqual(int('0x00',16), mem.get(556))  # av6[0] msb
        self.assertEqual(int('0x00',16), mem.get(555))  # av7[1] lsb
        self.assertEqual(int('0x1b',16), mem.get(554))  # av7[1] msl (27 dec)
        self.assertEqual(int('0x00',16), mem.get(553))  # av7[0] lsb
        self.assertEqual(int('0x07',16), mem.get(552))  # av7[0] msb


    def testSim(self):
        filename = 'test/types.elf'
        cu_name = 'test/types.ino.cpp'
        proc = "atmega2560"
        speed = 16000000
        sc = pysimulavr.SystemClock.Instance()
        sc.ResetClock()
        pysimulavr.DumpManager.Instance().Reset()
        pysimulavr.DumpManager.Instance().SetSingleDeviceApp()
        dev = pysimulavr.AvrFactory.instance().makeDevice(proc)
        dev.Load(filename)
        dev.SetClockFreq(10**9 / speed)
        sc.Add(dev)
        sc.RunTimeRange(speed)

        mem = SimMemory(dev)
        variables = dwarf.Globals(mem, filename, cu_name)

        self.checkPrimitiveRead(variables, 'v1', 2, 1, 648, True) # bool => bool
        self.checkPrimitiveRead(variables, 'v2', 2, 1, 647, True) # bool => bool
        self.checkPrimitiveRead(variables, 'v3', 8, 1, 646, 16) # uchar => int
        self.checkPrimitiveRead(variables, 'v4', 6, 1, 645, 17) # char => int
        self.checkPrimitiveRead(variables, 'v5', 4, 4, 641, 4.14, True) # float(aka double) => float
        self.checkPrimitiveRead(variables, 'v6', 4, 4, 637, 5.15, True) # float => float
        self.checkPrimitiveRead(variables, 'v7', 5, 2, 635, 15) # short(aka int) => short
        self.checkPrimitiveRead(variables, 'v8', 5, 4, 631, 16) # long(aka int) => int
        self.checkPrimitiveRead(variables, 'v9', 5, 2, 629, 17) # short => short
        self.checkPrimitiveRead(variables, 'v10', 7, 2, 627, 18) # size_t(uint16) => short
        self.checkPrimitiveRead(variables, 'v11', 8, 1, 626, 18) # uchar => short
        self.checkPrimitiveRead(variables, 'v12', 7, 2, 624, 19) # uint(16) => short
        self.checkPrimitiveRead(variables, 'v13', 7, 4, 620, 20) # uint(32) => int
        self.checkPrimitiveRead(variables, 'v14', 7, 2, 618, 21) # uint(16) => int

        self.checkArrayRead(variables, 'av1', 1, 2, 1, 578, 579, False, True)
        self.checkArrayRead(variables, 'av2', 1, 2, 1, 576, 577, True, False)
        self.checkArrayRead(variables, 'av3', 1, 8, 1, 574, 575, 1, 2)
        self.checkArrayRead(variables, 'av4', 1, 6, 1, 572, 573, 9, 8)
        self.checkArrayRead(variables, 'av5', 1, 4, 4, 564, 568, 1.4, 1.5, True)
        self.checkArrayRead(variables, 'av6', 1, 4, 4, 556, 560, 1.2, 1.3, True)
        self.checkArrayRead(variables, 'av7', 1, 5, 2, 552, 554, 9, 8)
        self.checkArrayRead(variables, 'av8', 1, 5, 4, 544, 548, 1, 2)
        self.checkArrayRead(variables, 'av9', 1, 5, 2, 540, 542, 2, 4)
        self.checkArrayRead(variables, 'av10', 1, 7, 2, 536, 538, 3, 2)
        self.checkArrayRead(variables, 'av11', 1, 8, 1, 534, 535, 4, 8)
        self.checkArrayRead(variables, 'av12', 1, 7, 2, 530, 532, 4, 1)
        self.checkArrayRead(variables, 'av13', 1, 7, 4, 522, 526, 9, 8)
        self.checkArrayRead(variables, 'av14', 1, 7, 2, 518, 520, 9, 7)

        self.checkStructRead(variables, 'sv1', 's1v1', 2, 1, 584, True)
        self.checkStructRead(variables, 'sv1', 's1v2', 2, 1, 585, True)
        self.checkStructRead(variables, 'sv1', 's1v3', 8, 1, 586, 1)
        self.checkStructRead(variables, 'sv1', 's1v4', 6, 1, 587, 2)
        self.checkStructRead(variables, 'sv1', 's1v5', 4, 4, 588, 3.14159, True)
        self.checkStructRead(variables, 'sv1', 's1v6', 4, 4, 592, 3.14159, True)
        self.checkStructRead(variables, 'sv1', 's1v7', 5, 2, 596, 3)
        self.checkStructRead(variables, 'sv1', 's1v8', 5, 4, 598, 4)
        self.checkStructRead(variables, 'sv1', 's1v9', 5, 2, 602, 5)
        self.checkStructRead(variables, 'sv1', 's1v10', 7, 2, 604, 1)
        self.checkStructRead(variables, 'sv1', 's1v11', 8, 1, 606, 3)
        self.checkStructRead(variables, 'sv1', 's1v12', 7, 2, 607, 6)
        self.checkStructRead(variables, 'sv1', 's1v13', 7, 4, 609, 7)
        self.checkStructRead(variables, 'sv1', 's1v14', 7, 2, 613, 8)
        self.checkStructRead(variables, 'sv1', 's1v15', 8, 1, 615, 15, False, 4, 4)
        self.checkStructRead(variables, 'sv1', 's1v16', 8, 1, 615, 4, False, 4, 0)
        self.checkStructRead(variables, 'sv1', 's1v17', 8, 1, 616, 3, False, 4, 4)
        self.checkStructRead(variables, 'sv1', 's1v18', 8, 1, 616, True, False, 1, 3)
        self.checkStructRead(variables, 'sv1', 's1v19', 8, 1, 616, 3, False, 3, 0)
        self.checkStructRead(variables, 'sv1', 's1v20', 8, 1, 617, 3, False, 2, 6)
        self.checkStructRead(variables, 'sv1', 's1v21', 8, 1, 617, 2, False, 2, 4)
        self.checkStructRead(variables, 'sv1', 's1v22', 8, 1, 617, 2, False, 2, 2)
        # TODO: something about pointers

    def testMask(self):
        self.assertEqual(15, dwarf.Primitive.mask(1,4,4))  # 0f = 15
        self.assertEqual(240, dwarf.Primitive.mask(1,4,0))  # f0 = 240

    def testSimAddrs(self):
        filename = 'test/types.elf'
        cu_name = 'test/types.ino.cpp'
        proc = "atmega2560"
        speed = 16000000
        sc = pysimulavr.SystemClock.Instance() # a fucking singleton
        sc.ResetClock()
        pysimulavr.DumpManager.Instance().Reset()
        pysimulavr.DumpManager.Instance().SetSingleDeviceApp()
        dev = pysimulavr.AvrFactory.instance().makeDevice(proc)
        dev.Load(filename)
        dev.SetClockFreq(10**9 / speed)
        sc.Add(dev)

        self.assertEqual(648, dev.data.GetAddressAtSymbol("v1"))
        self.assertEqual(647, dev.data.GetAddressAtSymbol("v2"))
        self.assertEqual(646, dev.data.GetAddressAtSymbol("v3"))
        self.assertEqual(645, dev.data.GetAddressAtSymbol("v4"))
        self.assertEqual(641, dev.data.GetAddressAtSymbol("v5"))
        self.assertEqual(637, dev.data.GetAddressAtSymbol("v6"))
        self.assertEqual(635, dev.data.GetAddressAtSymbol("v7"))
        self.assertEqual(631, dev.data.GetAddressAtSymbol("v8"))
        self.assertEqual(629, dev.data.GetAddressAtSymbol("v9"))
        self.assertEqual(627, dev.data.GetAddressAtSymbol("v10"))
        self.assertEqual(626, dev.data.GetAddressAtSymbol("v11"))
        self.assertEqual(624, dev.data.GetAddressAtSymbol("v12"))
        self.assertEqual(620, dev.data.GetAddressAtSymbol("v13"))
        self.assertEqual(618, dev.data.GetAddressAtSymbol("v14"))

        self.assertEqual(578, dev.data.GetAddressAtSymbol("av1"))
        self.assertEqual(576, dev.data.GetAddressAtSymbol("av2"))
        self.assertEqual(574, dev.data.GetAddressAtSymbol("av3"))
        self.assertEqual(572, dev.data.GetAddressAtSymbol("av4"))
        self.assertEqual(564, dev.data.GetAddressAtSymbol("av5"))
        self.assertEqual(556, dev.data.GetAddressAtSymbol("av6"))
        self.assertEqual(552, dev.data.GetAddressAtSymbol("av7"))
        self.assertEqual(544, dev.data.GetAddressAtSymbol("av8"))
        self.assertEqual(540, dev.data.GetAddressAtSymbol("av9"))
        self.assertEqual(536, dev.data.GetAddressAtSymbol("av10"))
        self.assertEqual(534, dev.data.GetAddressAtSymbol("av11"))
        self.assertEqual(530, dev.data.GetAddressAtSymbol("av12"))
        self.assertEqual(522, dev.data.GetAddressAtSymbol("av13"))
        self.assertEqual(518, dev.data.GetAddressAtSymbol("av14"))

        self.assertEqual(584, dev.data.GetAddressAtSymbol("sv1"))

        sc.RunTimeRange(speed)

        mem = SimMemory(dev)
        variables = dwarf.Globals(mem, filename, cu_name)

        self.assertEqual(int('0x01',16), mem.get(648))  # av1 bool
        self.assertEqual(int('0x01',16), mem.get(647))  # av2 bool
        self.assertEqual(int('0x10',16), mem.get(646))  # av3 uchar
        self.assertEqual(int('0x11',16), mem.get(645))  # av4 char

        self.assertEqual(int('0x01',16), mem.get(584))  # s1v1 true
        self.assertEqual(int('0x01',16), mem.get(585))  # s1v2 true
        self.assertEqual(int('0x01',16), mem.get(586))  # s1v3 1
        self.assertEqual(int('0x02',16), mem.get(587))  # s1v4 2
        self.assertEqual(int('0xd0',16), mem.get(588))  # s1v5.0 float 3.14159
        self.assertEqual(int('0x0f',16), mem.get(589))  # s1v5.1
        self.assertEqual(int('0x49',16), mem.get(590))  # s1v5.2
        self.assertEqual(int('0x40',16), mem.get(591))  # s1v5.3
        self.assertEqual(int('0xd0',16), mem.get(592))  # s1v6.0 float 3.14159
        self.assertEqual(int('0x0f',16), mem.get(593))  # s1v6.1
        self.assertEqual(int('0x49',16), mem.get(594))  # s1v6.2
        self.assertEqual(int('0x40',16), mem.get(595))  # s1v6.3
        self.assertEqual(int('0x03',16), mem.get(596))  # s1v7.0 int16 lsb
        self.assertEqual(int('0x00',16), mem.get(597))  # s1v7.1       msb
        self.assertEqual(int('0x04',16), mem.get(598))  # s1v8.0 int32 lsb
        self.assertEqual(int('0x00',16), mem.get(599))  # s1v8.1
        self.assertEqual(int('0x00',16), mem.get(600))  # s1v8.2
        self.assertEqual(int('0x00',16), mem.get(601))  # s1v8.3
        self.assertEqual(int('0x05',16), mem.get(602))  # s1v9.0 int16 lsb
        self.assertEqual(int('0x00',16), mem.get(603))  # s1v9.1
        self.assertEqual(int('0x01',16), mem.get(604))  # s1v10.0 int16
        self.assertEqual(int('0x00',16), mem.get(605))  # s1v10.1
        self.assertEqual(int('0x03',16), mem.get(606))  # s1v11  uchar8
        self.assertEqual(int('0x06',16), mem.get(607))  # s1v12.0 uint16
        self.assertEqual(int('0x00',16), mem.get(608))  # s1v12.1
        self.assertEqual(int('0x07',16), mem.get(609))  # s1v13.0 uint32
        self.assertEqual(int('0x00',16), mem.get(610))  # s1v13.1
        self.assertEqual(int('0x00',16), mem.get(611))  # s1v13.2
        self.assertEqual(int('0x00',16), mem.get(612))  # s1v13.3
        self.assertEqual(int('0x08',16), mem.get(613))  # s1v14.0 uint16
        self.assertEqual(int('0x00',16), mem.get(614))  # s1v14.1

        # i think offset is counting from MSB, which is wrong
        # see http://dwarfstd.org/ShowIssue.php?issue=081130.1

        # s1v15 4 bits 4 offset value 15 1111
        # s1v16 4 bits 0 offset value 4 0100
        self.assertEqual(int('0x4f',16), mem.get(615))  #  [v16 0100] [v15 1111]

        # s1v17 4 bits  4 offset value  3 0011
        # s1v18 1 bits  3 offset value  1    1
        # s1v19 3 bits  0 offset value  3  011
        self.assertEqual(int('0x73',16), mem.get(616))  # [v19 011] [v18 1] [v17 0101]

        # s1v20 2 bits 6 offset value 3  => 11
        # s1v21 2 bits 4 offset value 2  => 10
        # s1v22 2 bits 2 offset value 2  => 10
        self.assertEqual(int('0x2b',16), mem.get(617))  # 00101011 [00] [v22 10] [v21 10] [v20 11]

        self.assertEqual(int('0x01',16), mem.get(579))  # av1[1] ?
        self.assertEqual(int('0x00',16), mem.get(578))  # av1[0] av1
        self.assertEqual(int('0x00',16), mem.get(577))  # av2[1]
        self.assertEqual(int('0x01',16), mem.get(576))  # av2[0] av2
        self.assertEqual(int('0x02',16), mem.get(575))  # av3[1]
        self.assertEqual(int('0x01',16), mem.get(574))  # av3[0] av3
        self.assertEqual(int('0x08',16), mem.get(573))  # av4[1]
        self.assertEqual(int('0x09',16), mem.get(572))  # av4[0] av4
        self.assertEqual(int('0x3f',16), mem.get(571))  # 
        self.assertEqual(int('0xc0',16), mem.get(570))  # 
        self.assertEqual(int('0x00',16), mem.get(569))  # 
        self.assertEqual(int('0x00',16), mem.get(568))  # av5[1]
        self.assertEqual(int('0x3f',16), mem.get(567))  # 
        self.assertEqual(int('0xb3',16), mem.get(566))  # 
        self.assertEqual(int('0x33',16), mem.get(565))  # 
        self.assertEqual(int('0x33',16), mem.get(564))  # av5[0] av5



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TypesTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
