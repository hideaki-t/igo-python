# -*- coding: utf-8 -*-
import sys
from igo.dictreader import DictReader


if sys.version_info[0] > 2:
    unichr = chr


def base_id(nid):
    """
    BASEノードに格納するID値をエンコードするためのメソッド
    BASEノードに格納されているID値をデコードするためにも用いられる
    """
    return (-nid) - 1


chck_TERMINATE_CODE = 0
"""
文字列の終端を表す文字コード

この文字はシステムにより予約されており、辞書内の形態素の表層形および解析対象テキストに含まれていた場合の動作は未定義
"""

chck_VACANT_CODE = 1
"""
CHECKノードが未使用だということを示すための文字コード

この文字はシステムにより予約されており、辞書内の形態素の表層形および解析対象テキストに含まれていた場合の動作は未定義
"""

chck_CODE_LIMIT = 0xFFFF
"""
使用可能な文字の最大値
"""


class KeyStream:
    """
    文字列を文字のストリームとして扱うためのクラス。
    readメソッドで個々の文字を順に読み込み、文字列の終端に達した場合には{@code Chck_TERMINATE_CODE}が返される。
    * XXX: クラス名は不適切
    """
    __slots__ = ['s', 'cur', 'len']

    def __init__(self, key, start=0):
        self.s = key
        self.cur = start
        self.len = len(key)

    def startswith(self, prefix):
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
            return chck_TERMINATE_CODE
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
    __slots__ = ['rd', 'num_keys', 'begs', 'base', 'lens', 'chck', 'tail']

    def __init__(self, path, bigendian=False, use_mmap=None):
        """
        instantiate a DoubleArray Searcher

        @param filepath path of DoubleArray
        @param mmap use mmap or not; None: depends on environment
        """
        self.rd = DictReader(path, bigendian, use_mmap)
        with self.rd as r:
            node_size = r.get_int()
            tind_size = r.get_int()
            tail_size = r.get_int()
            self.num_keys = tind_size
            self.begs = r.get_intarray(tind_size)
            self.base = r.get_intarray(node_size)
            self.lens = r.get_shortarray(tind_size)
            self.chck = r.get_chararray(node_size)
            self.tail = r.get_chararray(tail_size)

    def release(self):
        del self.begs
        del self.base
        del self.lens
        del self.chck
        del self.tail
        self.rd.release()
        del self.rd

    def size(self):
        """
        DoubleArrayに格納されているキーの数を返す
        @return DoubleArrayに格納されているキー数
        """
        return self.num_keys

    def search(self, key):
        """
        キーを検索する

        @param key 検索対象のキー文字列
        @return キーが見つかった場合はそのIDを、見つからなかった場合は-1を返す
        """
        begs = self.begs
        tail = self.tail
        lens = self.lens
        base = self.base
        chck = self.chck
        node = base[0]

        def exists(kin, node):
            node_id = base_id(node)
            beg = begs[node_id]
            s = tail[beg:beg + lens[node_id]]
            return kin.rest().equals(s)

        kin = KeyStream(key)
        code = kin.read()
        while 1:
            idx = node + code
            node = base[idx]
            if chck[idx] == code:
                if node >= 0:
                    continue
                elif kin.eos() or exists(kin, node):
                    return base_id(node)
            return -1

# with, iterator
    def commonprefix_search(self, key, start, fn):
        """
        common-prefix検索を行う
        条件に一致するキーが見つかる度に、fn.call(...)メソッドが呼び出される

        @param key 検索対象のキー文字列
        @param start 検索対象となるキー文字列の最初の添字
        @param fn 一致を検出した場合に呼び出されるメソッドを定義したコールバック関数
        """
        base = self.base
        chck = self.chck
        begs = self.begs
        tail = self.tail
        lens = self.lens
        node = base[0]
        offset = -1
        kin = KeyStream(key, start)

        def call_if_key_including(kin, node, start, offset, fn):
            node_id = base_id(node)
            l = lens[node_id]
            beg = begs[node_id]
            prefix = tail[beg:beg+l]
            if kin.startswith(prefix):
                fn(start, offset + l + 1, node_id)

        while 1:
            code = kin.read()
            offset += 1
            terminal_idx = node + chck_TERMINATE_CODE
            if chck[terminal_idx] == chck_TERMINATE_CODE:
                fn(start, offset, base_id(base[terminal_idx]))
                if code == chck_TERMINATE_CODE:
                    return
            idx = node + code
            node = base[idx]
            if chck[idx] == code:
                if node >= 0:
                    continue
                else:
                    call_if_key_including(kin, node, start, offset, fn)
            return
