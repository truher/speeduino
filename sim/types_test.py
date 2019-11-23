import unittest
import dwarf
import pysimulavr

class TypesTest(unittest.TestCase):

    def testTrue(self):
        self.assertTrue(True)

    def checkPrimitive(self, variables, varname, encoding, size, location, value):
        v = variables.variable(varname)
        self.assertEqual('Primitive', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        self.assertEqual(encoding, v.encoding())
        self.assertEqual(size, v.byte_size())
        self.assertEqual(location, v.location())   
        self.assertEqual(0, v.read())  # default is 0
        v.write(value)
        self.assertEqual(value, v.read())

    def checkArray(self, variables, varname, upper_bound, encoding, size, location0, location1, value0, value1):
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
        self.assertEqual(0, e0.read())
        e1 = v.get(1)
        self.assertEqual(location1, e1.location())   
        self.assertEqual(0, e1.read())
        e0.write(value0)
        e1.write(value1)
        self.assertEqual(value0, e0.read())
        self.assertEqual(value1, e1.read())

    def checkStruct(self, variables, varname, membername, encoding, size, location, value):
        v = variables.variable(varname)
        self.assertEqual('Struct', v.__class__.__name__)
        self.assertEqual('DW_TAG_variable', v.var_die.tag)
        e0 = v.member(membername)
        self.assertEqual('Primitive', e0.__class__.__name__)
        self.assertEqual('DW_TAG_member', e0.var_die.tag)
        self.assertEqual(encoding, e0.encoding())
        self.assertEqual(size, e0.byte_size())
        self.assertEqual(location, e0.location())   
        self.assertEqual(0, e0.read())
        e0.write(value)
        self.assertEqual(value, e0.read())

    # check initial values without running the code
    def testDwarf(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem,
            '.pio/build/megaatmega2560/firmware.elf',
            'src/types.ino.cpp')

        self.checkPrimitive(variables, 'v1', 2, 1, 645, True) # bool => bool
        self.checkPrimitive(variables, 'v2', 2, 1, 644, True) # bool => bool
        self.checkPrimitive(variables, 'v3', 8, 1, 643, 3) # uchar => int
        self.checkPrimitive(variables, 'v4', 6, 1, 642, 4) # char => int
        self.checkPrimitive(variables, 'v5', 4, 4, 638, 5.5) # float(aka double) => float
        self.checkPrimitive(variables, 'v6', 4, 4, 634, 6.5) # float => float
        self.checkPrimitive(variables, 'v7', 5, 2, 632, 7) # short(aka int) => short
        self.checkPrimitive(variables, 'v8', 5, 4, 628, 8) # long(aka int) => int
        self.checkPrimitive(variables, 'v9', 5, 2, 626, 9) # short => short
        self.checkPrimitive(variables, 'v10', 7, 2, 624, 10) # size_t(uint16) => short
        self.checkPrimitive(variables, 'v11', 8, 1, 623, 11) # uchar => short
        self.checkPrimitive(variables, 'v12', 7, 2, 621, 12) # uint(16) => short
        self.checkPrimitive(variables, 'v13', 7, 4, 617, 13) # uint(32) => int
        self.checkPrimitive(variables, 'v14', 7, 2, 615, 14) # uint(16) => int

        # TODO: fix these locations

        self.checkArray(variables, 'av1', 1, 2, 1, 613, 612, True, True)
        self.checkArray(variables, 'av2', 1, 2, 1, 611, 610, True, True)
        self.checkArray(variables, 'av3', 1, 8, 1, 609, 608, 3, 4)
        self.checkArray(variables, 'av4', 1, 6, 1, 607, 606, 4, 5)
        self.checkArray(variables, 'av5', 1, 4, 4, 599, 595, 5.5, 6.5)
        self.checkArray(variables, 'av6', 1, 4, 4, 591, 587, 6.5, 7.5) # this is wrong
        self.checkArray(variables, 'av7', 1, 5, 2, 587, 585, 7, 8)
        self.checkArray(variables, 'av8', 1, 5, 4, 579, 575, 8, 9)     # this is wrong
        self.checkArray(variables, 'av9', 1, 5, 2, 575, 573, 9, 10)
        self.checkArray(variables, 'av10', 1, 7, 2, 571, 569, 10, 11)
        self.checkArray(variables, 'av11', 1, 8, 1, 569, 568, 11, 12)
        self.checkArray(variables, 'av12', 1, 7, 2, 565, 563, 12, 13)
        self.checkArray(variables, 'av13', 1, 7, 4, 557, 553, 13, 14)  # this is wrong
        self.checkArray(variables, 'av14', 1, 7, 2, 553, 551, 14, 15)

        self.checkStruct(variables, 'sv1', 's1v1', 2, 1, 522, True)
        self.checkStruct(variables, 'sv1', 's1v2', 2, 1, 523, True)
        self.checkStruct(variables, 'sv1', 's1v3', 8, 1, 524, 3)
        self.checkStruct(variables, 'sv1', 's1v4', 6, 1, 525, 4)
        self.checkStruct(variables, 'sv1', 's1v5', 4, 4, 526, 5.5)
        self.checkStruct(variables, 'sv1', 's1v6', 4, 4, 530, 6.5)
        self.checkStruct(variables, 'sv1', 's1v7', 5, 2, 534, 7)
        self.checkStruct(variables, 'sv1', 's1v8', 5, 4, 536, 8)
        self.checkStruct(variables, 'sv1', 's1v9', 5, 2, 540, 9)
        self.checkStruct(variables, 'sv1', 's1v10', 7, 2, 542, 10)
        self.checkStruct(variables, 'sv1', 's1v11', 8, 1, 544, 11)
        self.checkStruct(variables, 'sv1', 's1v12', 7, 2, 545, 12)
        self.checkStruct(variables, 'sv1', 's1v13', 7, 4, 547, 13)
        self.checkStruct(variables, 'sv1', 's1v14', 7, 2, 551, 14)

        # TODO: make the pointers work

        # vv0 = variables.variable('vv0')
        # self.assertEqual(34, vv0.get(0).read())
        # vv1 = variables.variable('vv1')
        # self.assertEqual('\x10', vv1.get(0).read())

    def testDwarf(self):
        sc = pysimulavr.SystemClock.Instance()
        pysimulavr.DumpManager.Instance().SetSingleDeviceApp()
        dev = pysimulavr.AvrFactory.instance().makeDevice("atmega2560")
        dev.Load('.pio/build/megaatmega2560/firmware.elf')
        dev.SetClockFreq(10**9 / 16000000)
        sc.Add(dev)
        self.assertEqual(645, dev.data.GetAddressAtSymbol("v1"))
        self.assertEqual(644, dev.data.GetAddressAtSymbol("v2"))
        self.assertEqual(643, dev.data.GetAddressAtSymbol("v3"))
        self.assertEqual(642, dev.data.GetAddressAtSymbol("v4"))
        self.assertEqual(638, dev.data.GetAddressAtSymbol("v5"))
        self.assertEqual(634, dev.data.GetAddressAtSymbol("v6"))
        self.assertEqual(632, dev.data.GetAddressAtSymbol("v7"))
        self.assertEqual(628, dev.data.GetAddressAtSymbol("v8"))
        self.assertEqual(626, dev.data.GetAddressAtSymbol("v9"))
        self.assertEqual(624, dev.data.GetAddressAtSymbol("v10"))
        self.assertEqual(623, dev.data.GetAddressAtSymbol("v11"))
        self.assertEqual(621, dev.data.GetAddressAtSymbol("v12"))
        self.assertEqual(617, dev.data.GetAddressAtSymbol("v13"))
        self.assertEqual(615, dev.data.GetAddressAtSymbol("v14"))

        # TODO: something about arrays
        # TODO: something about pointers

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TypesTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
