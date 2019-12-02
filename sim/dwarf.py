#!/usr/bin/env python
#
# see http://dwarfstd.org/doc/DWARF4.pdf

from elftools.elf.elffile import ELFFile
from elftools.dwarf.descriptions import (describe_attr_value, describe_DWARF_expr, set_global_machine_arch)
from elftools.dwarf.locationlists import (LocationEntry, LocationExpr, LocationParser)
from elftools.dwarf.dwarf_expr import (GenericExprVisitor, DW_OP_opcode2name)
import struct
import binascii
import memory

## represents the memory of the device
#class Memory():
#    def get(self,addr):      # int
#        raise NotImplementedError()
#    def set(self,addr,val):  # int
#        raise NotImplementedError()
#
## internal python, for testing and maybe page flipping?
## the cpp equivalent has another wrapper (one per byte) with a hook for tracing
## and it pre-initializes the whole range
#class DictMemory(Memory):
#    def __init__(self):
#        self.rw = {}
#    def get(self, addr):      # int
#        if addr not in self.rw:
#            return 0
#        return self.rw[addr]
#    def set(self, addr, val): # int
#        if not isinstance(val, int):
#            raise ValueError("wrong value type: %s " % type(val))
#        self.rw[addr] = val

# this visitor thing is how you get at the decoder
class OpVal(GenericExprVisitor):
    def __init__(self, structs, op):
        super(OpVal, self).__init__(structs)
        self.val = 0
        self.op = op

    def _after_visit(self, opcode, opcode_name, args):
        if opcode_name == self.op:
            self.val = args[0]

# represents the collection of all the variables in the dwarf
class Globals:
    def __init__(self, memory, elf_file_name, cu_name):
        self.memory = memory
        self.cu_name = cu_name
        self.dwarf = Dwarf(elf_file_name)
        self.cu_die = self.dwarf.getCuDie(cu_name)

    def variable(self, var_name):
        # check that var_name exists
        var_die = self.dwarf.getVarDie(self.cu_die, var_name)
        if var_die is None:
            raise ValueError("invalid variable name %s" % var_name)
        return Variable.factory(self.memory, self.cu_name, var_die, None, self.dwarf)

    def getAllVarNames(self):
        result = []
        cu_die = self.dwarf.getCuDie(self.cu_name)
        for die in cu_die.iter_children():
            if die.tag != 'DW_TAG_variable':
                continue
            if 'DW_AT_name' not in die.attributes:
                continue
            result.append(die.attributes['DW_AT_name'].value)
        return result

class Variable:
    def __init__(self, memory, var_die, parent, dwarf, index=0):
        self.memory = memory
        self.var_die = var_die
        self.dwarf = dwarf
        self.parent = parent
        self.index = index # used by arrays; TODO push it over there

    # location means RAM offset
    def location(self):
        parent_location = 0 if self.parent is None else self.parent.location()
        location = parent_location + self.dwarf.getLocation(self.var_die)
        return location
        
    def name(self):
        return self.var_die.attributes['DW_AT_name'].value

    @staticmethod
    def factory(memory, cu_name, var_die, parent, dwarf):
        if dwarf.isStruct(cu_name, var_die):
            return Struct(memory, var_die, parent, dwarf)
        elif dwarf.isArray(cu_name, var_die):
            return Array(memory, var_die, parent, dwarf)
        else:
            return Primitive(memory, var_die, parent, dwarf)
        raise ValueError("unknown type")

class Struct(Variable):
    def member(self, member_name):
        type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
        for member_die in type_die.iter_children():
            if member_die.tag != 'DW_TAG_member':
                raise ValueError("wrong tag for name %s" % member_name)
            if member_name == member_die.attributes['DW_AT_name'].value:
                return Primitive(self.memory, member_die, self, self.dwarf)
        raise ValueError("no member named %s % member_name")

    def getAllMemberNames(self):
        result = []
        type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
        for member_die in type_die.iter_children():
            if 'DW_AT_name' not in member_die.attributes:
                raise ValueError("no member name")
            if member_die.tag != 'DW_TAG_member':
                continue
            result.append(member_die.attributes['DW_AT_name'].value)
        return result

class Array(Variable):
# todo change this to "element"
    def get(self, index):
        if index > self.upper_bound():
            raise ValueException("index %d greater than upper bound %d" % (index, upper_bound))
        return Primitive(self.memory, self.var_die, self, self.dwarf, index)

    def upper_bound(self):
        type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
        for child_die in type_die.iter_children():
            if child_die.tag == 'DW_TAG_subrange_type':
                return child_die.attributes['DW_AT_upper_bound'].value
        raise ValueException("no upper bound")

    def size(self):
        return self.upper_bound() + 1

#        type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
#        for die in type_die.iter_children():
#            if die.tag == 'DW_TAG_subrange_type':
#                return die.attributes['DW_AT_upper_bound'].value + 1
#        raise ValueError("could not find upper bound")

    def location(self):
        parent_location = 0 if self.parent is None else self.parent.location()
        return parent_location + self.dwarf.getLocation(self.var_die)

class Primitive(Variable):
    @staticmethod
    def mask(byte_size, bit_size, bit_offset):
        if byte_size > 1:
            raise ValueError("multi-byte masks are not supported")
        binstr = '0b' + '0' *  bit_offset + '1' * bit_size + '0' * (8 - bit_offset - bit_size)
        binint = int(binstr , 2)
        return binint
        
    def read(self):
        if 'DW_AT_const_value' in self.var_die.attributes:
            return self.var_die.attributes['DW_AT_const_value'].value
        encoding = self.encoding()
        byte_size = self.byte_size()

        # see https://docs.python.org/2.7/library/struct.html
        # see http://dwarfstd.org/doc/DWARF4.pdf

        location = self.location()
        if encoding == 2 and byte_size == 1:  # DW bool => py bool
            memval = self.memory.get(location)
            return struct.unpack('?', '%s' % chr(memval))[0]

        if encoding == 4 and byte_size == 4: # float (also double, maybe because atmega?) => float
            memval = self.memory.get(location)
            memval1 = self.memory.get(location+1)
            memval2 = self.memory.get(location+2)
            memval3 = self.memory.get(location+3)
            return struct.unpack('f', '%s%s%s%s' % (chr(memval), chr(memval1), chr(memval2), chr(memval3)))[0]  

        if encoding == 5 and byte_size == 2: # signed int (16)
            memval = self.memory.get(location)
            memval1 = self.memory.get(location+1)
            # python unsigned short == dwarf unsigned int
            return struct.unpack('h', '%s%s' % (chr(memval), chr(memval1)))[0]  

        if encoding == 5 and byte_size == 4: # signed int (32)
            memval = self.memory.get(location)
            memval1 = self.memory.get(location+1)
            memval2 = self.memory.get(location+2)
            memval3 = self.memory.get(location+3)
            return struct.unpack('i', '%s%s%s%s' % (chr(memval), chr(memval1), chr(memval2), chr(memval3)))[0]  

        if encoding == 6 and byte_size == 1:  # DW signed char => int
            memval = self.memory.get(location)
            return struct.unpack('b', '%s' % chr(memval))[0]

        if encoding == 7 and byte_size == 2: # unsigned int (16)
            memval = self.memory.get(location)
            memval1 = self.memory.get(location+1)
            # python unsigned short == dwarf unsigned int
            return struct.unpack('H', '%s%s' % (chr(memval), chr(memval1)))[0]  

        if encoding == 7 and byte_size == 4: # unsigned int (32)
            memval = self.memory.get(location)
            memval1 = self.memory.get(location+1)
            memval2 = self.memory.get(location+2)
            memval3 = self.memory.get(location+3)
            return struct.unpack('I', '%s%s%s%s' % (chr(memval), chr(memval1), chr(memval2), chr(memval3)))[0]  

        if encoding == 8 and byte_size == 1:  # DW unsigned char => int
            memval = self.memory.get(location)
            bit_size = self.bit_size()
            bit_offset = self.bit_offset()
            if bit_size is not None and bit_offset is not None:
                # TOOD: this is a tiny part of the bit field possibilities, do the rest.
                memval &= Primitive.mask(byte_size, bit_size, bit_offset)
                shift = 8 - bit_size - bit_offset
                memval = memval >> shift
            return struct.unpack('B', '%s' % chr(memval))[0]

        raise ValueError("unknown encoding %d or byte_size %d" % (encoding, byte_size))

    def write(self, value):
        if 'DW_AT_const_value' in self.var_die.attributes:
            raise ValueError("const value")
        encoding = self.encoding()
        byte_size = self.byte_size()

        if encoding == 2 and byte_size == 1:  # bool
            if value < 0 or value > 1:
                raise ValueError("value out of bounds")
            memval = struct.pack('?', value)
            location = self.location()
            self.memory.set(location, bytearray(memval)[0])
            return

        if encoding == 4 and byte_size == 4:  # float (also double, maybe because atmega?) => float
            memval = struct.pack('f', value)
            location = self.location()
            for i,x in enumerate(bytearray(memval)):
                self.memory.set(location+i, x)
            return

        if encoding == 5 and byte_size == 2: # signed int 16
            if not isinstance(value, int):
                raise ValueError("value not integral")
            if value < -32768 or value > 32767:
                raise ValueError("value out of bounds")
            memval = struct.pack('h', value)
            location = self.location()
            for i,x in enumerate(bytearray(memval)):
                self.memory.set(location + i, x)
            return

        if encoding == 5 and byte_size == 4: # signed int 32
            if not isinstance(value, int):
                raise ValueError("value not integral")
            if value < -2147483648 or value > 2147483647:
                raise ValueError("value out of bounds")
            memval = struct.pack('i', value)
            location = self.location()
            for i,x in enumerate(bytearray(memval)):
                self.memory.set(location + i, x)
            return

        if encoding == 6 and byte_size == 1:  # DW signed char => int
            if not isinstance(value, int):
                raise ValueError("value not integral")
            if value < -128 or value > 127:
                raise ValueError("value out of bounds")
            memval = struct.pack('b', value)
            location = self.location()
            for i,x in enumerate(bytearray(memval)):
                self.memory.set(location + i, x)
            return

        if encoding == 7 and byte_size == 2: # unsigned int
            if not isinstance(value, int):
                raise ValueError("value not integral")
            if value < 0 or value > 65535:
                raise ValueError("value out of bounds")
            memval = struct.pack('H', value)  # python unsigned short == dwarf unsigned int
            location = self.location()
            for i,x in enumerate(bytearray(memval)):
                self.memory.set(location + i, x)
            return

        if encoding == 7 and byte_size == 4: # unsigned long
            if not isinstance(value, int):
                raise ValueError("value not integral")
            if value < 0 or value > 4294967295:
                raise ValueError("value out of bounds")
            memval = struct.pack('I', value)
            location = self.location()
            for i,x in enumerate(bytearray(memval)):
                self.memory.set(location + i, x)
            return

        if encoding == 8 and byte_size == 1:  # unsigned char
            if not isinstance(value, int):
                raise ValueError("value not integral")
            if value < 0 or value > 255:
                raise ValueError("value out of bounds")
            memval = struct.pack('B', value)
            memval = bytearray(memval)[0]
            location = self.location()

            byte_size = self.byte_size()
            bit_size = self.bit_size()
            bit_offset = self.bit_offset()
            if bit_size is not None and bit_offset is not None:
                max_value = (1 << bit_size) - 1
                if value > max_value:
                    raise ValueError("value %d out of bounds %d" % (value, max_value))
                # TOOD: this is a tiny part of the bit field possibilities, do the rest.
                shift = 8 - bit_size - bit_offset
                memval = memval << shift
                mask = Primitive.mask(byte_size, bit_size, bit_offset)
                memval &= mask
                oldval = self.memory.get(location)
                oldval &= ~mask
                memval |= oldval
            self.memory.set(location, memval)
            return

        raise ValueError("unknown encoding %d or byte_size %d" % (encoding, byte_size))

    def encoding(self):
        type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
        if type_die.tag == 'DW_TAG_array_type':   # the 'real' type is underneath
            type_die = self.dwarf.resolveTypeRef(self.var_die.cu.get_top_DIE(), type_die)
        if 'DW_AT_encoding' not in type_die.attributes:
            raise ValueError("no encoding %s" % type_die)
        return type_die.attributes['DW_AT_encoding'].value

    def location(self):
        if 'DW_AT_const_value' in self.var_die.attributes:
            raise ValueError("const value")
        parent_location = 0 if self.parent is None else self.parent.location()
        if self.var_die.tag == 'DW_TAG_variable':
            type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
            if type_die.tag == 'DW_TAG_array_type':   # don't count location twice
                return parent_location + self.index * self.byte_size()
            return parent_location + self.dwarf.getLocation(self.var_die) + self.index * self.byte_size()
        if self.var_die.tag == 'DW_TAG_member':
            opval = OpVal(self.var_die.cu.structs, 'DW_OP_plus_uconst')
            member_location_value = self.var_die.attributes['DW_AT_data_member_location'].value
            opval.process_expr(member_location_value)
            member_location = opval.val
            return parent_location + member_location
        raise ValueError("bad tag %s" % self.var_die.tag)

    # ignores the 'byte_size' included in fields with bit width, it looks like it's always the same
    # as the attribute of the 'type'
    def byte_size(self):
        #if self.var_die.tag == 'DW_TAG_member':
        #    if 'DW_AT_byte_size' not in self.var_die.attributes:
        #        raise ValueError("missing attr %s" % self.var_die)
        #    return self.var_die.attributes['DW_AT_byte_size'].value
        type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
        if type_die.tag == 'DW_TAG_array_type':
            # the 'real' type is underneath
            type_die = self.dwarf.resolveTypeRef(self.var_die.cu.get_top_DIE(), type_die)
        byte_size = type_die.attributes['DW_AT_byte_size'].value
        return byte_size

    def bit_size(self):
        if self.var_die.tag != 'DW_TAG_member':
            return None
        if 'DW_AT_bit_size' not in self.var_die.attributes:
            return None
        return self.var_die.attributes['DW_AT_bit_size'].value
        #type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
        #bit_size = type_die.attributes['DW_AT_bit_size'].value
        #return byte_size

    def bit_offset(self):
        if self.var_die.tag != 'DW_TAG_member':
            return None
        if 'DW_AT_bit_offset' not in self.var_die.attributes:
            return None
        return self.var_die.attributes['DW_AT_bit_offset'].value
        #type_die = self.dwarf.resolveType(self.var_die.cu.get_top_DIE(), self.var_die)
        #bit_offset = type_die.attributes['DW_AT_bit_offset'].value
        #return byte_size

class Dwarf:
    def __init__(self, filename):
        self.file = open(filename, 'rb')
        self.elffile = ELFFile(self.file)
        self.dwarfinfo = self.elffile.get_dwarf_info()
        self.section_offset = self.dwarfinfo.debug_info_sec.global_offset
        self.location_lists = self.dwarfinfo.location_lists()
        set_global_machine_arch(self.elffile.get_machine_arch())
        self.loc_parser = LocationParser(self.location_lists)
        if not self.dwarfinfo.has_debug_info:
            raise ValueError("no debug info found in file %s" % filename)

    def __del__(self):
        self.file.close()

    def getAll(self):
        cu_die = self.getCuDie(cu_name)
        for die in cu_die.iter_children():
            if die.tag != 'DW_TAG_variable':
                continue
            if 'DW_AT_name' not in die.attributes:
                continue
            name = die.attributes['DW_AT_name'].value

    def isArray(self, cu_name, var_die):
        cu_die = self.getCuDie(cu_name)
        typeDie = self.resolveType(cu_die, var_die)
        return typeDie.tag == 'DW_TAG_array_type'

    def isStruct(self, cu_name, var_die):
        cu_die = self.getCuDie(cu_name)
        typeDie = self.resolveType(cu_die, var_die)
        return typeDie.tag == 'DW_TAG_structure_type'

    # get the base type die for the specified die
    def resolveType(self, cu_die, die):
        if die.tag == 'DW_TAG_base_type':
            if 'DW_AT_name' not in die.attributes: raise ValueError("base type has no name")
            if 'DW_AT_byte_size' not in die.attributes: raise ValueError("base type has no byte size")
            if 'DW_AT_encoding' not in die.attributes: raise ValueError("base type has no encoding")
            name_attr = die.attributes['DW_AT_name']
            if name_attr.form not in ('DW_FORM_string', 'DW_FORM_strp'):
                raise ValueError("base type name form is wrong")
            byte_size_attr = die.attributes['DW_AT_byte_size']
            if byte_size_attr.form not in ('DW_FORM_data1'):
                raise ValueError("base type byte size form is wrong")
            encoding_attr = die.attributes['DW_AT_encoding']
            if encoding_attr.form not in ('DW_FORM_data1'):
                raise ValueError("base type encoding form is wrong")
            return die
        elif die.tag == 'DW_TAG_volatile_type':
            # ignore "volatile" wrapper
            return self.resolveTypeRef(cu_die, die)
        elif die.tag == 'DW_TAG_array_type':
            # stop at array so we can see the location
            return die
        elif die.tag == 'DW_TAG_pointer_type':
            # TODO: handle like arrays?
            raise ValueError("pointers are unsupported %s" % die.tag)
        elif die.tag == 'DW_TAG_const_type':
            return self.resolveTypeRef(cu_die, die)
        elif die.tag == 'DW_TAG_member':
            return self.resolveTypeRef(cu_die, die)
        elif die.tag == 'DW_TAG_typedef':
            return self.resolveTypeRef(cu_die, die)
        elif die.tag == 'DW_TAG_variable':
            return self.resolveTypeRef(cu_die, die)
        elif die.tag == 'DW_TAG_structure_type':
            # struct is the base type
            return die
        raise ValueError("weird tag %s" % die.tag)

    # get the die corresponding to the type reference of the given die
    def resolveTypeRef(self, cu_die, die):
        type_attr = die.attributes['DW_AT_type']
        if type_attr is None or type_attr.form != 'DW_FORM_ref4':
            raise ValueError("wrong form for type reference")
        # the ref is relative
        type_offset = type_attr.value + cu_die.cu.cu_offset
        type_die = self.getDieByOffset(cu_die, type_offset)
        return self.resolveType(cu_die, type_die)

    # get the die at (absolute) offset in the dwarf stream
    def getDieByOffset(self, cu_die, offset):
        for die in cu_die.iter_children():
            if die.offset == offset:
                return die
        raise ValueError("couldn't find offset")

    # get memory location by var_die
    def getLocation(self, var_die):
        for attr in var_die.attributes.itervalues():
            if self.loc_parser.attribute_has_location(attr, var_die.cu['version']):
                loc = self.loc_parser.parse_from_attribute(attr, var_die.cu['version'])
                if not isinstance(loc, LocationExpr):
                    raise ValueError("wrong location type")
                opval = OpVal(var_die.cu.structs, 'DW_OP_addr')
                opval.process_expr(loc.loc_expr)
                if opval == 0:
                    raise ValueError("zero location, variable is not used")
                return opval.val - 8388608
        raise ValueError("couldn't find location")

    # get compilation unit by name
    def getCuDie(self, name):
        for cu in self.dwarfinfo.iter_CUs():
            for die in cu.iter_DIEs():
                if die.tag != 'DW_TAG_compile_unit':
                    continue
                if 'DW_AT_name' in die.attributes and die.attributes['DW_AT_name'].value == name:
                    return die
        raise ValueError("couldn't find compilation unit %s" % name)

    # get variable die by name
    def getVarDie(self, cu_die, name):
        for die in cu_die.iter_children():
            if die.tag != 'DW_TAG_variable':
                continue
            if 'DW_AT_name' in die.attributes and die.attributes['DW_AT_name'].value == name:
                return die
        raise ValueError("couldn't find variable die %s" % name)

