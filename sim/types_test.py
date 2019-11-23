import unittest
import dwarf
import pysimulavr
import ctypes

class SimMemory(dwarf.Memory):
    def __init__(self, dev):
        self.dev = dev
    def get(self, addr):
        return chr(self.dev.GetRWMem(addr))
    def set(self, addr, val):
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
        #self.assertEqual(0, v.read())  # default is 0
        v.write(value)
        self.assertEqual(value, v.read())

    def checkPrimitiveRead(self, variables, varname, encoding, size, location, value, approx=False):
        v = variables.variable(varname)
        self.assertEqual('Primitive', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        self.assertEqual(encoding, v.encoding())
        self.assertEqual(size, v.byte_size())
        self.assertEqual(location, v.location())   
        #self.assertEqual(0, v.read())  # default is 0
        #v.write(value)
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
        #self.assertEqual(0, e0.read())
        e1 = v.get(1)
        self.assertEqual(encoding, e1.encoding())
        self.assertEqual(size, e1.byte_size())
        self.assertEqual(location1, e1.location())   
        #self.assertEqual(0, e1.read())
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
        #self.assertEqual(0, e0.read())
        e1 = v.get(1)
        self.assertEqual(encoding, e1.encoding())
        self.assertEqual(size, e1.byte_size())
        self.assertEqual(location1, e1.location())   
        #self.assertEqual(0, e1.read())
        #e0.write(value0)
        #e1.write(value1)
        if approx:
            self.assertAlmostEqual(value0, e0.read(), 2)
            self.assertAlmostEqual(value1, e1.read(), 2)
        else:
            self.assertEqual(value0, e0.read())
            self.assertEqual(value1, e1.read())

    def checkStructWriteReadback(self, variables, varname, membername, encoding, size, location, value):
        v = variables.variable(varname)
        self.assertEqual('Struct', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        e0 = v.member(membername)
        self.assertEqual('Primitive', e0.__class__.__name__)
        self.assertEqual('DW_TAG_member', e0.var_die.tag)
        self.assertEqual(encoding, e0.encoding())
        self.assertEqual(size, e0.byte_size())
        self.assertEqual(location, e0.location())   
        #self.assertEqual(0, e0.read())
        e0.write(value)
        self.assertEqual(value, e0.read())

    def checkStructRead(self, variables, varname, membername, encoding, size, location, value):
        v = variables.variable(varname)
        self.assertEqual('Struct', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        e0 = v.member(membername)
        self.assertEqual('Primitive', e0.__class__.__name__)
        self.assertEqual('DW_TAG_member', e0.var_die.tag)
        self.assertEqual(encoding, e0.encoding())
        self.assertEqual(size, e0.byte_size())
        self.assertEqual(location, e0.location())   
        #self.assertEqual(0, e0.read())
        #e0.write(value)
        self.assertEqual(value, e0.read())

    # check initial values without running the code
    def testDwarf(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem,
            'test/types.elf',
            'test/types.ino.cpp')

        self.checkPrimitiveWriteReadback(variables, 'v1', 2, 1, 649, True) # bool => bool
        self.checkPrimitiveWriteReadback(variables, 'v2', 2, 1, 648, True) # bool => bool
        self.checkPrimitiveWriteReadback(variables, 'v3', 8, 1, 647, 3) # uchar => int
        self.checkPrimitiveWriteReadback(variables, 'v4', 6, 1, 646, 4) # char => int
        self.checkPrimitiveWriteReadback(variables, 'v5', 4, 4, 642, 5.5) # float(aka double) => float
        self.checkPrimitiveWriteReadback(variables, 'v6', 4, 4, 638, 6.5) # float => float
        self.checkPrimitiveWriteReadback(variables, 'v7', 5, 2, 636, 7) # short(aka int) => short
        self.checkPrimitiveWriteReadback(variables, 'v8', 5, 4, 632, 8) # long(aka int) => int
        self.checkPrimitiveWriteReadback(variables, 'v9', 5, 2, 630, 9) # short => short
        self.checkPrimitiveWriteReadback(variables, 'v10', 7, 2, 628, 10) # size_t(uint16) => short
        self.checkPrimitiveWriteReadback(variables, 'v11', 8, 1, 627, 11) # uchar => short
        self.checkPrimitiveWriteReadback(variables, 'v12', 7, 2, 625, 12) # uint(16) => short
        self.checkPrimitiveWriteReadback(variables, 'v13', 7, 4, 621, 13) # uint(32) => int
        self.checkPrimitiveWriteReadback(variables, 'v14', 7, 2, 619, 14) # uint(16) => int

        self.checkArrayWriteReadback(variables, 'av1', 1, 2, 1, 578, 579, True, True)
        self.checkArrayWriteReadback(variables, 'av2', 1, 2, 1, 576, 577, True, True)
        self.checkArrayWriteReadback(variables, 'av3', 1, 8, 1, 574, 575, 3, 23)
        self.checkArrayWriteReadback(variables, 'av4', 1, 6, 1, 572, 573, 4, 24)
        self.checkArrayWriteReadback(variables, 'av5', 1, 4, 4, 564, 568, 5.5, 25.5)
        self.checkArrayWriteReadback(variables, 'av6', 1, 4, 4, 556, 560, 6.5, 26.5)
        self.checkArrayWriteReadback(variables, 'av7', 1, 5, 2, 552, 554, 7, 27)

        self.assertEqual('\x18', mem.get(573))  # av4[1] (24 dec)
        self.assertEqual('\x04', mem.get(572))  # av4[0]
        self.assertEqual('\x41', mem.get(571))  # av5[1] lsb
        self.assertEqual('\xcc', mem.get(570))  #
        self.assertEqual('\x00', mem.get(569))  #
        self.assertEqual('\x00', mem.get(568))  # av5[1] msb
        self.assertEqual('\x40', mem.get(567))  # av5[0] lsb
        self.assertEqual('\xb0', mem.get(566))  # 
        self.assertEqual('\x00', mem.get(565))  # 
        self.assertEqual('\x00', mem.get(564))  # av5[0] msb
        self.assertEqual('\x41', mem.get(563))  # av6[1] lsb
        self.assertEqual('\xd4', mem.get(562))  # 
        self.assertEqual('\x00', mem.get(561))  #
        self.assertEqual('\x00', mem.get(560))  # av6[1] msb
        self.assertEqual('\x40', mem.get(559))  # av6[0] lsb
        self.assertEqual('\xd0', mem.get(558))  #
        self.assertEqual('\x00', mem.get(557))  #
        self.assertEqual('\x00', mem.get(556))  # av6[0] msb
        self.assertEqual('\x00', mem.get(555))  # av7[1] lsb
        self.assertEqual('\x1b', mem.get(554))  # av7[1] msl (27 dec)
        self.assertEqual('\x00', mem.get(553))  # av7[0] lsb
        self.assertEqual('\x07', mem.get(552))  # av7[0] msb

        
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

        self.checkStructWriteReadback(variables, 'sv1', 's1v15', 7, 1, -1, 15) # uint(4) => int
        self.checkStructWriteReadback(variables, 'sv1', 's1v16', 5, 1, -1, -4) # int(4) => int
        self.checkStructWriteReadback(variables, 'sv1', 's1v17', 5, 1, -1, -3) # int(4) => int
        self.checkStructWriteReadback(variables, 'sv1', 's1v18', 2, 1, -1, True) # bool => bool
        self.checkStructWriteReadback(variables, 'sv1', 's1v19', 7, 1, -1, '\x03') # byte(4) => int
        self.checkStructWriteReadback(variables, 'sv1', 's1v20', 5, 1, -1, 3) # int(4) => int
        self.checkStructWriteReadback(variables, 'sv1', 's1v21', 5, 1, -1, 3) # int(4) => int
        self.checkStructWriteReadback(variables, 'sv1', 's1v22', 5, 1, -1, 3) # int(4) => int

        # TODO: make the pointers work

        # vv0 = variables.variable('vv0')
        # self.assertEqual(34, vv0.get(0).read())
        # vv1 = variables.variable('vv1')
        # self.assertEqual('\x10', vv1.get(0).read())

    def testSim(self):
        filename = 'test/types.elf'
        cu_name = 'test/types.ino.cpp'
        proc = "atmega2560"
        speed = 16000000
        sc = pysimulavr.SystemClock.Instance()
        pysimulavr.DumpManager.Instance().SetSingleDeviceApp()
        dev = pysimulavr.AvrFactory.instance().makeDevice(proc)
        dev.Load(filename)

        self.assertEqual(649, dev.data.GetAddressAtSymbol("v1"))
        self.assertEqual(648, dev.data.GetAddressAtSymbol("v2"))
        self.assertEqual(647, dev.data.GetAddressAtSymbol("v3"))
        self.assertEqual(646, dev.data.GetAddressAtSymbol("v4"))
        self.assertEqual(642, dev.data.GetAddressAtSymbol("v5"))
        self.assertEqual(638, dev.data.GetAddressAtSymbol("v6"))
        self.assertEqual(636, dev.data.GetAddressAtSymbol("v7"))
        self.assertEqual(632, dev.data.GetAddressAtSymbol("v8"))
        self.assertEqual(630, dev.data.GetAddressAtSymbol("v9"))
        self.assertEqual(628, dev.data.GetAddressAtSymbol("v10"))
        self.assertEqual(627, dev.data.GetAddressAtSymbol("v11"))
        self.assertEqual(625, dev.data.GetAddressAtSymbol("v12"))
        self.assertEqual(621, dev.data.GetAddressAtSymbol("v13"))
        self.assertEqual(619, dev.data.GetAddressAtSymbol("v14"))

        dev.SetClockFreq(10**9 / speed)
        sc.Add(dev)
        sc.RunTimeRange(speed)

        mem = SimMemory(dev)
        variables = dwarf.Globals(mem, filename, cu_name)

        self.assertEqual('\x01', mem.get(649))  # av1 bool
        self.assertEqual('\x01', mem.get(648))  # av2 bool
        self.assertEqual('\x10', mem.get(647))  # av3 uchar
        self.assertEqual('\x11', mem.get(646))  # av4 char

        self.checkPrimitiveRead(variables, 'v1', 2, 1, 649, True) # bool => bool
        self.checkPrimitiveRead(variables, 'v2', 2, 1, 648, True) # bool => bool
        self.checkPrimitiveRead(variables, 'v3', 8, 1, 647, 16) # uchar => int
        self.checkPrimitiveRead(variables, 'v4', 6, 1, 646, 17) # char => int
        self.checkPrimitiveRead(variables, 'v5', 4, 4, 642, 4.14, True) # float(aka double) => float
        self.checkPrimitiveRead(variables, 'v6', 4, 4, 638, 5.15, True) # float => float
        self.checkPrimitiveRead(variables, 'v7', 5, 2, 636, 15) # short(aka int) => short
        self.checkPrimitiveRead(variables, 'v8', 5, 4, 632, 16) # long(aka int) => int
        self.checkPrimitiveRead(variables, 'v9', 5, 2, 630, 17) # short => short
        self.checkPrimitiveRead(variables, 'v10', 7, 2, 628, 18) # size_t(uint16) => short
        self.checkPrimitiveRead(variables, 'v11', 8, 1, 627, 18) # uchar => short
        self.checkPrimitiveRead(variables, 'v12', 7, 2, 625, 19) # uint(16) => short
        self.checkPrimitiveRead(variables, 'v13', 7, 4, 621, 20) # uint(32) => int
        self.checkPrimitiveRead(variables, 'v14', 7, 2, 619, 21) # uint(16) => int

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

        self.assertEqual('\x01', mem.get(579))  # av1[1] ?
        self.assertEqual('\x00', mem.get(578))  # av1[0] av1
        self.assertEqual('\x00', mem.get(577))  # av2[1]
        self.assertEqual('\x01', mem.get(576))  # av2[0] av2
        self.assertEqual('\x02', mem.get(575))  # av3[1]
        self.assertEqual('\x01', mem.get(574))  # av3[0] av3
        self.assertEqual('\x08', mem.get(573))  # av4[1]
        self.assertEqual('\x09', mem.get(572))  # av4[0] av4
        self.assertEqual('?', mem.get(571))  # 
        self.assertEqual('\xc0', mem.get(570))  # 
        self.assertEqual('\x00', mem.get(569))  # 
        self.assertEqual('\x00', mem.get(568))  # av5[1]
        self.assertEqual('?', mem.get(567))  # 
        self.assertEqual('\xb3', mem.get(566))  # 
        self.assertEqual('3', mem.get(565))  # 
        self.assertEqual('3', mem.get(564))  # av5[0] av5

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

        # TODO: something about arrays
        # TODO: something about pointers

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TypesTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
