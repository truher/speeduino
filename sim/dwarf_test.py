import unittest
import dwarf

# TODO: embed the type name in the wrapper

class TestDwarf(unittest.TestCase):

    def test_nonexistent_global(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        with self.assertRaises(ValueError):
            variables.variable('no_such_variable')

    def test_struct_primitive(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        # struct config4
        configPage4 = variables.variable('configPage4')
        self.assertEqual("Struct", configPage4.__class__.__name__)
        self.assertEqual("DW_TAG_variable", configPage4.var_die.tag)
        # int16_t
        triggerAngle = configPage4.member("triggerAngle") # signed int16
        self.assertEqual("Primitive", triggerAngle.__class__.__name__)
        self.assertEqual("DW_TAG_member", triggerAngle.var_die.tag)
        self.assertEqual(5, triggerAngle.encoding())
        self.assertEqual(3846, triggerAngle.location())               # (in this particular elf file)
        self.assertEqual(0, triggerAngle.read(), 'default should be 0')
        triggerAngle.write(1)
        self.assertDictEqual({3846:1, 3847:0}, mem.rw)
        self.assertEqual(1, triggerAngle.read())
        triggerAngle.write(32767)  # it's int16
        self.assertDictEqual({3846:255, 3847:127}, mem.rw)
        self.assertEqual(32767, triggerAngle.read())
        triggerAngle.write(-32768)  # it's int16
        self.assertDictEqual({3846:0, 3847:128}, mem.rw)
        self.assertEqual(-32768, triggerAngle.read())
        with self.assertRaises(Exception):
            triggerAngle.write(123456)  # because it's too wide
        with self.assertRaises(Exception):
            triggerAngle.write(3.14159)  # because it's not an int

    def test_const_primitive(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        # const byte
        dsv = variables.variable('data_structure_version')
        # (in this particular elf file)
        self.assertEqual("0x1d831", hex(dsv.var_die.offset))
        self.assertEqual("Primitive", dsv.__class__.__name__)
        self.assertEqual("DW_TAG_variable", dsv.var_die.tag)
        self.assertEqual(8, dsv.encoding())      # 8 = unsigned char
        self.assertEqual(2, dsv.read())
        with self.assertRaises(ValueError):      # because it's const
            dsv.write(1)
        with self.assertRaises(ValueError):      # because it's const
            dsv.location()
        self.assertDictEqual({}, mem.rw)         # because nothing was written
        self.assertEqual(2, dsv.read())          # still the const value
        with self.assertRaises(Exception):
            dsv.write("this should not work")    # because it's too long

    def test_byte_primitive(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        # byte
        fpt = variables.variable('fpPrimeTime')
        self.assertEqual("0x1df2d", hex(fpt.var_die.offset)) # (in this particular elf file)
        self.assertEqual("Primitive", fpt.__class__.__name__)
        self.assertEqual("DW_TAG_variable", fpt.var_die.tag)
        self.assertEqual(8, fpt.encoding())                  # unsigned char
        self.assertEqual(4975, fpt.location())               # (in this particular elf file)
        self.assertEqual(0, fpt.read())                      # zero is default
        fpt.write(1)
        self.assertDictEqual({4975:1}, mem.rw)
        self.assertEqual(1, fpt.read())
        with self.assertRaises(Exception):
            fpt.write("this should not work")                # because it's too long

    def test_uint16_primitive(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        # byte
        mlc = variables.variable('mainLoopCount')
        self.assertEqual("0x1df41", hex(mlc.var_die.offset)) # (in this particular elf file)
        self.assertEqual("Primitive", mlc.__class__.__name__)
        self.assertEqual("DW_TAG_variable", mlc.var_die.tag)
        self.assertEqual(7, mlc.encoding())                  # unsigned long int
        self.assertEqual(4973, mlc.location())               # (in this particular elf file)
        self.assertEqual(0, mlc.read())                      # zero is default
        mlc.write(1)
        self.assertDictEqual({4973:'\x01', 4974:'\x00'}, mem.rw)  # little endian
        self.assertEqual(1, mlc.read())
        with self.assertRaises(Exception):
            mlc.write(100000)                                # because it's too big

    def test_uint16_primitive(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        # byte
        rt = variables.variable('revolutionTime')
        self.assertEqual("0x1df55", hex(rt.var_die.offset)) # (in this particular elf file)
        self.assertEqual("Primitive", rt.__class__.__name__)
        self.assertEqual("DW_TAG_variable", rt.var_die.tag)
        self.assertEqual(7, rt.encoding())                  # unsigned long
        self.assertEqual(4969, rt.location())               # (in this particular elf file)
        self.assertEqual(0, rt.read())                      # zero is default
        rt.write(1)
        self.assertDictEqual({4969:1, 4970:0, 4971:0, 4972:0}, mem.rw)
        self.assertEqual(1, rt.read())
        with self.assertRaises(Exception):
            rt.write(42949672950)                                # because it's too big

    def test_bool_primitive(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        # byte
        rt = variables.variable('clutchTrigger')
        self.assertEqual("0x1dfa5", hex(rt.var_die.offset)) # (in this particular elf file)
        self.assertEqual("Primitive", rt.__class__.__name__)
        self.assertEqual("DW_TAG_variable", rt.var_die.tag)
        self.assertEqual(2, rt.encoding())                  # bool
        self.assertEqual(4962, rt.location())               # (in this particular elf file)
        self.assertEqual(0, rt.read())                      # zero is default
        rt.write(1)
        self.assertDictEqual({4962:1}, mem.rw)
        self.assertEqual(1, rt.read())
        with self.assertRaises(Exception):
            rt.write(3)                                # because it's too big

    def test_array(self):
        mem = dwarf.DictMemory()
        variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
        # uint16_t[12]
        nps = variables.variable('npage_size')
        self.assertEqual("Array", nps.__class__.__name__)
        self.assertEqual("DW_TAG_variable", nps.var_die.tag)
        self.assertEqual(12, nps.size())
        # uint16_t
        npsval = nps.get(0)
        self.assertEqual(7, npsval.encoding())
        self.assertEqual(0, npsval.read()) # default
        npsval.write(1)
        self.assertDictEqual({698:1, 699:0}, mem.rw)
        self.assertEqual(1, npsval.read())


    # TODO: make pointers work
    #
    #def test_struct_array(self):
    #    mem = dwarf.DictMemory()
    #    variables = dwarf.Globals(mem, 'test/speeduino.elf', 'speeduino/speeduino.ino.cpp')
    #    # struct table3D
    #    ft = variables.variable('fuelTable')
    #    self.assertEqual("Struct", ft.__class__.__name__)
    #    # byte**  weird that it's actually a 2d array, why do that?
    #    values = ft.member("values")
    #    self.assertEqual("Array", values.__class__.__name__)
    #    val0 = values.get(0)
    #    self.assertEqual("Array", val0.__class__.__name__)
    #    val00 = val0.get(0)
    #    self.assertEqual("Primitive", val00.__class__.__name__)
    #    self.assertEqual(0, val00.read())
    #    # byte*
    #    axisX = ft.member("axisX")
    #    axisX0 = axisX.get(0)
    #    self.assertEqual(0, axisX0.read())

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDwarf)
    unittest.TextTestRunner(verbosity=2).run(suite)
