# -*- coding: utf-8 -*-
import sys
from igo.dictreader import DictReader


if sys.version_info[0] > 2:
    unichr = chr


class Node:
    """
    DoubleArrayのノード用の定数などが定義されているクラス
    """
    class Base:
        """ BASEノード用の定数およびメソッドが定義されているクラス """

        @staticmethod
        def ID(nid):
            """
            BASEノードに格納するID値をエンコードするためのメソッド
            BASEノードに格納されているID値をデコードするためにも用いられる
            """
            return (-nid) - 1

    class Chck:
        """
        CHECKノード用の定数が定義されているクラス
        """
        TERMINATE_CODE = 0
        """
        文字列の終端を表す文字コード

        この文字はシステムにより予約されており、辞書内の形態素の表層形および解析対象テキストに含まれていた場合の動作は未定義
        """

        VACANT_CODE = 1
        """
        CHECKノードが未使用だということを示すための文字コード

        この文字はシステムにより予約されており、辞書内の形態素の表層形および解析対象テキストに含まれていた場合の動作は未定義
        """

        CODE_LIMIT = 0xFFFF
        """
        使用可能な文字の最大値
        """


class KeyStream:
    """
    文字列を文字のストリームとして扱うためのクラス。
    readメソッドで個々の文字を順に読み込み、文字列の終端に達した場合には{@code Node.Chck.TERMINATE_CODE}が返される。
    * XXX: クラス名は不適切
    """

    def __init__(self, key, start=0):
        self.s = key
        self.cur = start
        self.len = len(key)

    def startsWith(self, prefix):
        cur = self.cur
        s = self.s
        length = len(prefix)

        if self.len - cur < length:
            return False
        return s[cur:cur + length] == prefix

    def rest(self):
        return self.s[self.cur:]

    def read(self):
        if self.eos():
            return Node.Chck.TERMINATE_CODE
        else:
            p = self.cur
            self.cur += 1
            return self.s[p]

    def eos(self):
        return self.cur == self.len


class Searcher:
    """
    DoubleArray検索用のクラス
    """
    def __init__(self, filepath, bigendian=False):
        """
        保存されているDoubleArrayを読み込んで、このクラスのインスタンスを作成する

        @param filepath DoubleArrayが保存されているファイルのパス
        @throws IOException filepathで示されるファイルの読み込みに失敗した場合に送出される
        """
        with DictReader(filepath, bigendian) as r:
            nodeSz = r.getInt()
            tindSz = r.getInt()
            tailSz = r.getInt()
            self.keySetSize = tindSz
            self.begs = r.getIntArray(tindSz)
            self.base = r.getIntArray(nodeSz)
            self.lens = r.getShortArray(tindSz)
            self.chck = r.getCharArray(nodeSz)
            self.tail = r.getCharArray(tailSz)

    def size(self):
        """
        DoubleArrayに格納されているキーの数を返す
        @return DoubleArrayに格納されているキー数
        """
        return self.keySetSize

    def search(self, key):
        """
        キーを検索する

        @param key 検索対象のキー文字列
        @return キーが見つかった場合はそのIDを、見つからなかった場合は-1を返す
        """
        base = self.base
        chck = self.chck
        keyExists = self.keyExists

        node = base[0]
        kin = KeyStream(key)
        code = kin.read()
        while 1:
            idx = node + code
            node = base[idx]
            if chck[idx] == code:
                if node >= 0:
                    continue
                elif kin.eos() or keyExists(kin, node):
                    return Node.Base.ID(node)
            return -1

# with, iterator
    def eachCommonPrefix(self, key, start, fn):
        """
        common-prefix検索を行う
        条件に一致するキーが見つかる度に、fn.call(...)メソッドが呼び出される

        @param key 検索対象のキー文字列
        @param start 検索対象となるキー文字列の最初の添字
        @param fn 一致を検出した場合に呼び出されるメソッドを定義したコールバック関数
        """
        base = self.base
        chck = self.chck
        node = base[0]
        offset = -1
        kin = KeyStream(key, start)

        while 1:
            code = kin.read()
            offset += 1
            terminalIdx = node + Node.Chck.TERMINATE_CODE
            if chck[terminalIdx] == Node.Chck.TERMINATE_CODE:
                fn(start, offset, Node.Base.ID(base[terminalIdx]))
                if code == Node.Chck.TERMINATE_CODE:
                    return
            idx = node + code
            node = base[idx]
            if chck[idx] == code:
                if node >= 0:
                    continue
                else:
                    self.call_if_keyIncluding(kin, node, start, offset, fn)
            return

    def call_if_keyIncluding(self, kin, node, start, offset, fn):
        nodeId = Node.Base.ID(node)
        l = self.lens[nodeId]
        beg = self.begs[nodeId]
        prefix = self.tail[beg:beg+l]
        if kin.startsWith(prefix):
            fn(start, offset + l + 1, nodeId)

    def keyExists(self, kin, node):
        nodeId = Node.Base.ID(node)
        beg = self.begs[nodeId]
        s = self.tail[beg:beg + self.lens[nodeId]]
        return kin.rest().equals(s)
