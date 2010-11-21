# -*- coding: utf-8 -*-
import mmap
import struct
import array

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
        self.f = open(filepath, 'rb')
        self.mmap = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)

    def getInt(self):
        b = self.mmap.read(4)
        return struct.unpack('@i', b)[0]

    def getIntArray(self, elementCount):
        ary = array.array('i')
        ary.fromstring(self.mmap.read(elementCount*4))
        #cur = m.tell()
        #end = cur+elementCount*4
        #ary.fromstring(m[cur:end])
        #m.seek(end)
        return ary

    def getShortArray(self, elementCount):
        ary = array.array('h')
        ary.fromstring(self.mmap.read(elementCount*2))
        #cur = m.tell()
        #end = cur+elementCount*2
        #ary.fromstring(m[cur:end])
        #m.seek(end)
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
        self.mmap.close()
        self.f.close()
