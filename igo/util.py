# -*- coding: utf-8 -*-
import array
import codecs
import os
import struct


if hasattr(os, 'fstat'):

    def size(f):
        return os.fstat(f.fileno()).st_size
else:

    def size(f):
        return os.stat(f.name).st_size

littleendian = struct.pack('@i', 1)[0] == '\x01'


class filewrapper(file):
    def size(self):
        return size(self)


class FileMappedInputStream:
    """
    ファイルにマッピングされた入力ストリーム<br />
    igo以下のモジュールではファイルからバイナリデータを取得する場合、必ずこのクラスが使用される
    """
    INT_NATIVE = '@i'
    INT_BIG_ENDIAN = '!i'
    SHORT_NATIVE = '@h'
    SHORT_BIG_ENDIAN = '!h'

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
            self.short_fmt = '!h'
            self.byteswap = self.swap if littleendian and bigendian else self.nop
            self.char_encoding = 'UTF-16-BE'
        else:
            self.int_fmt = '@i'
            self.short_fmt = '@h'
            self.byteswap = self.nop
            self.char_encoding = 'UTF-16-LE' if littleendian else 'UTF-16-BE'
        self.f = filewrapper(filepath, 'rb')

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
        return codecs.getreader(self.char_encoding)(self.f).read(elementCount)

    def size(self):
        return self.f.size()

    def close(self):
        self.f.close()


def getIntArray(filepath, bigendian=False):
    fmis = FileMappedInputStream(filepath, bigendian)
    try:
        return fmis.getIntArray(fmis.size() / 4)
    finally:
        fmis.close()


def getCharArray(filepath, bigendian=False):
    fmis = FileMappedInputStream(filepath, bigendian)
    try:
        return fmis.getCharArray(fmis.size() / 2)
    finally:
        fmis.close()


def getCharArrayMulti(filepaths, bigendian=False):
    ary = array.array('H')
    for path in filepaths:
        f = open(path, 'rb')
        try:
            ary.fromfile(f, size(f) / 2)
        finally:
            f.close()
    if littleendian and bigendian:
        ary.byteswap()
    return ary
