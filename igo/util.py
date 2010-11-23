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

    def __init__(self, filepath):
        """
        入力ストリームを作成する

        @param filepath マッピングするファイルのパス
        """
        if mmap:
            self.f = open(filepath, 'rb')
            self.mmap = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        else:
            self.f = StringIO.StringIO()
            self.mmap = filewrapper(filepath, 'rb')

    def getInt(self):
        b = self.mmap.read(4)
        return struct.unpack('@i', b)[0]

    def getIntArray(self, elementCount):
        ary = array.array('i')
        ary.fromstring(self.mmap.read(elementCount*4))
        return ary

    def getShortArray(self, elementCount):
        ary = array.array('h')
        ary.fromstring(self.mmap.read(elementCount*2))
        return ary

    def getCharArray(self, elementCount):
        # srcformat is UTF-16
        return self.mmap.read(elementCount*2).decode('UTF-16')

    def getString(self, elementCount):
        return self.getCharArray(elementCount)

    @staticmethod
    def getIntArrayS(filepath):
        fmis = FileMappedInputStream(filepath)
        try:
            return fmis.getIntArray(fmis.size()/4)
        finally:
            fmis.close()

    @staticmethod
    def getStringS(filepath):
        fmis = FileMappedInputStream(filepath)
        try:
            return fmis.getString(fmis.size()/2)
        finally:
            fmis.close()

    def size(self):
	return self.mmap.size()

    def close(self):
        try:
            self.mmap.close()
        finally:
            self.f.close()
