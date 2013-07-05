# -*- coding: utf-8 -*-
from __future__ import division
import array
import codecs
import os
import struct
import sys

LE, UTF16Codec = (True, codecs.lookup('UTF-16-LE')) \
    if sys.byteorder == 'little' else (False, codecs.lookup('UTF-16-LE'))

if hasattr(os, 'fstat'):
    def size(f):
        return os.fstat(f.fileno()).st_size
else:
    def size(f):
        return os.stat(f.name).st_size


class FileMappedInputStream:
    """
    ファイルにマッピングされた入力ストリーム<br />
    igo以下のモジュールではファイルからバイナリデータを取得する場合、必ずこのクラスが使用される
    """

    @staticmethod
    def nop(a):
        pass

    @staticmethod
    def swap(a):
        a.byteswap()

    def __init__(self, filepath, bigendian=False):
        """
        入力ストリームを作成する

        @param filepath マッピングするファイルのパス
        @param bigendian big endianかどうか
        """
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

    def getInt(self):
        b = self.f.read(4)
        return struct.unpack(self.int_fmt, b)[0]

    def getIntArray(self, elementCount):
        ary = array.array('i')
        ary.fromfile(self.f, elementCount)
        self.byteswap(ary)
        return ary

    def getShortArray(self, elementCount):
        ary = array.array('h')
        ary.fromfile(self.f, elementCount)
        self.byteswap(ary)
        return ary

    def getCharArray(self, elementCount):
        ary = array.array('H')
        ary.fromfile(self.f, elementCount)
        self.byteswap(ary)
        return ary

    def getString(self, elementCount):
        return self.decoder(self.f.read(elementCount * 2))[0]

    def size(self):
        return size(self.f)

    def close(self):
        self.f.close()


def getIntArray(filepath, bigendian=False):
    fmis = FileMappedInputStream(filepath, bigendian)
    try:
        return fmis.getIntArray(fmis.size() // 4)
    finally:
        fmis.close()


def getCharArray(filepath, bigendian=False):
    fmis = FileMappedInputStream(filepath, bigendian)
    try:
        return fmis.getCharArray(fmis.size() // 2)
    finally:
        fmis.close()


def getCharArrayMulti(filepaths, bigendian=False):
    ary = array.array('H')
    for path in filepaths:
        f = open(path, 'rb')
        try:
            ary.fromfile(f, size(f) // 2)
        finally:
            f.close()
    if LE and bigendian:
        ary.byteswap()
    return ary
