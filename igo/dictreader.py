# -*- coding: utf-8 -*-
from __future__ import division
import array
import codecs
import os
import struct
import sys

LE, UTF16Codec = (True, codecs.lookup('UTF-16-LE')) \
    if sys.byteorder == 'little' else (False, codecs.lookup('UTF-16-LE'))

try:
    import mmap
    sizemap = {'i': 4, 'h': 2, 'H': 2}

    def checksize():
        from struct import Struct
        return set(sizemap.items()) == \
            set({x: Struct(x).size for x in 'ihH'}.items())
    allow_mmap = hasattr(memoryview, 'cast') and checksize() and LE
except:
    allow_mmap = False

if hasattr(os, 'fstat'):
    def size(f):
        return os.fstat(f.fileno()).st_size
else:
    def size(f):
        return os.stat(f.name).st_size


class StandardReader:
    """
    reader for dictionary files using normal file io
    """

    @staticmethod
    def nop(a):
        pass

    @staticmethod
    def swap(a):
        a.byteswap()

    def __init__(self, filepath, bigendian=False):
        if bigendian:
            self.int_fmt = '!i'
            """ big endian int32 """
            self.short_fmt = '!h'
            """ big endian int16 """
            self.byteswap = self.swap if LE and bigendian else self.nop
            self.decoder = codecs.getdecoder('UTF-16-BE')
        else:
            self.int_fmt = '=i'
            """ native int32 format """
            self.short_fmt = '=h'
            """ native int16 format """
            self.byteswap = self.nop
            self.decoder = UTF16Codec.decode
        self.f = open(filepath, 'rb')

    def __enter__(self):
        return self

    def __exit__(self, et, ev, t):
        self.close()

    def getInt(self):
        b = self.f.read(4)
        return struct.unpack(self.int_fmt, b)[0]

    def getIntArray(self, count=None):
        c = count if count is not None else (self.size() // 4)
        ary = array.array('i')
        ary.fromfile(self.f, c)
        self.byteswap(ary)
        return ary

    def getShortArray(self, count):
        ary = array.array('h')
        ary.fromfile(self.f, count)
        self.byteswap(ary)
        return ary

    def getCharArray(self, count=None):
        c = count if count is not None else (self.size() // 2)
        ary = array.array('H')
        ary.fromfile(self.f, c)
        self.byteswap(ary)
        return ary

    def size(self):
        return size(self.f)

    def close(self):
        if self.f:
            self.f.close()
            self.f = None

    def release(self):
        self.close()


class MMapedReader:
    """
    dictionary reader using mmap.
    this only can read native datasize/byte order dictonary
    """
    def __init__(self, path, bigendian=False):
        self.fd = os.open(path, os.O_RDONLY)
        self.mmap = mmap.mmap(self.fd, length=0, access=mmap.ACCESS_READ)
        self.view = memoryview(self.mmap)
        self.pos = 0

    def __enter__(self):
        return self

    def __exit__(self, et, ev, t):
        self.close()

    def _get(self, fmt, cnt):
        with memoryview(self.view[self.pos:]).cast(fmt) as view:
            # need to support endian conversion?
            # also size of types must be native
            self.pos += sizemap[fmt] * cnt
            return view[:cnt]

    def getInt(self):
        v = self._get('i', 1)[0]
        return v

    def getIntArray(self, count=None):
        c = count if count is not None else (self.size() // 4)
        return self._get('i', c)

    def getShortArray(self, count):
        return self._get('h', count)

    def getCharArray(self, count=None):
        c = count if count is not None else (self.size() // 2)
        return self._get('H', c)

    def size(self):
        return len(self.mmap)

    def close(self):
        # nothing to close, everything is mapped
        pass

    def release(self):
        self.view.release()
        self.mmap.close()
        os.close(self.fd)


def DictReader(f, b=False, use_mmap=None):
    m = allow_mmap if use_mmap is None else use_mmap
    if m:
        return MMapedReader(f, b)
    else:
        return StandardReader(f, b)


# this is only used for splitted dictionary mode
# no mmap version provided for now
def getCharArrayMulti(filepaths, bigendian=False):
    ary = array.array('H')
    for path in filepaths:
        with open(path, 'rb') as f:
            ary.fromfile(f, size(f) // 2)
    if LE and bigendian:
        ary.byteswap()
    return ary
