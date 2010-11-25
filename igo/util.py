# -*- coding: utf-8 -*-
import struct
import array

try:
    import mmap
except:
    mmap = None
    import os
    import StringIO

    class filewrapper(file):
        def size(self):
            return os.fstat(self.fileno()).st_size


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
            self.byteswap = self.swap
            self.char_encoding = 'UTF-16-BE'
        else:
            self.int_fmt = '@i'
            self.short_fmt = '@h'
            self.byteswap = self.nop
            self.char_encoding = 'UTF-16'
        if mmap:
            self.f = open(filepath, 'rb')
            self.mmap = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        else:
            self.f = StringIO.StringIO()
            self.mmap = filewrapper(filepath, 'rb')

    def getInt(self):
        b = self.mmap.read(4)
        return struct.unpack(self.int_fmt, b)[0]

    def getIntArray(self, elementCount):
        ary = array.array('i')
        ary.fromstring(self.mmap.read(elementCount * 4))
        self.byteswap(ary)
        return ary

    def getShortArray(self, elementCount):
        ary = array.array('h')
        ary.fromstring(self.mmap.read(elementCount * 2))
        self.byteswap(ary)
        return ary

    def getCharArray(self, elementCount):
        # srcformat is UTF-16
        return self.mmap.read(elementCount * 2).decode(self.char_encoding)

    def getString(self, elementCount):
        return self.getCharArray(elementCount)

    @staticmethod
    def getIntArrayS(filepath, bigendian=False):
        fmis = FileMappedInputStream(filepath, bigendian)
        try:
            return fmis.getIntArray(fmis.size() / 4)
        finally:
            fmis.close()

    @staticmethod
    def getStringS(filepath, bigendian=False):
        fmis = FileMappedInputStream(filepath, bigendian)
        try:
            return fmis.getString(fmis.size() / 2)
        finally:
            fmis.close()

    def size(self):
        return self.mmap.size()

    def close(self):
        try:
            self.mmap.close()
        finally:
            self.f.close()
