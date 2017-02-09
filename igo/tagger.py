# -*- coding: utf-8 -*-
from igo.dictionary import Matrix, WordDic, Unknown, ViterbiNode
from igo.dictreader import UTF16Codec
import os.path
from os.path import dirname, abspath
import array

decodeUTF16b = UTF16Codec.decode
try:
    UTF16Codec.decode(array.array('H', [0x3042]))

    def decodeUTF16a(a):
        return UTF16Codec.decode(a)
except:
    # for codec does not support an array
    print('fallback')

    def decodeUTF16a(a):
        return UTF16Codec.decode(a.tostring())


class Morpheme:
    """
    形態素クラス
    """
    __slots__ = ['surface', 'feature', 'start']

    def __init__(self, surface, feature, start):
        self.surface = surface
        """ 形態素の表層形 """
        self.feature = feature
        """ 形態素の素性 """
        self.start = start
        """ テキスト内での形態素の出現開始位置 """

    def __str__(self):
        return self.fmt()

    def fmt(self, fmt="surface: {surface}, feature: {feature}, start={start}"):
        return fmt.format(
            surface=self.surface, feature=self.feature, start=self.start)


class Tagger:
    """
    形態素解析を行うクラス
    """
    __slots__ = ['wdc', 'unk', 'mtx']
    __BOS_NODES = [ViterbiNode.makeBOSEOS()]

    @staticmethod
    def lookup():
        """
        モジュールが置いてある場所から辞書を探す
        @return: モジュール内で見つかった辞書のパス
        """
        path = os.path.join(abspath(dirname(__file__)), 'ipadic')
        if (os.path.exists(path)):
            return path
        return None

    def __init__(self, path=None, gae=False, use_mmap=None):
        """
        バイナリ辞書を読み込んで、形態素解析器のインスタンスを作成する

        @param path directory of a binary dictionary
        """
        if not path:
            path = Tagger.lookup()
        self.wdc = WordDic(path, gae, gae, use_mmap)
        self.unk = Unknown(path, gae, use_mmap)
        self.mtx = Matrix(path, gae, use_mmap)

    def parse(self, text, result=None):
        """
        形態素解析を行う

        @param text 解析対象テキスト
        @param result 解析結果の形態素が追加されるリスト. None指定時は内部でリストを作成する
        @return 解析結果の形態素リスト. {@code parse(text,result)=result}
        """
        if result is None:
            result = []
        text = array.array('H', UTF16Codec.encode(text)[0])
        vn = self.__parse(text)
        wd = self.wdc.word_data
        while vn:
            surface = decodeUTF16a(text[vn.start:vn.start + vn.length])[0]
            feature = decodeUTF16b(wd(vn.word_id))[0]
            result.append(Morpheme(surface, feature, vn.start))
            vn = vn.prev
        return result

    """
    分かち書きを行う

    @param text 分かち書きされるテキスト
    @param result 分かち書き結果の文字列が追加されるリスト. None指定時は内部でリストを作成する
    @return 分かち書きされた文字列のリスト. {@code wakati(text,result)=result}
    """

    def wakati(self, text, result=None):
        if result is None:
            result = []
        text = array.array('H', UTF16Codec.encode(text)[0])
        vn = self.__parse(text)
        while vn:
            result.append(decodeUTF16a(text[vn.start:vn.start + vn.length])[0])
            vn = vn.prev
        return result

    def __parse(self, text):
        length = len(text)
        nodes = [None] * (length + 1)
        nodes[0] = Tagger.__BOS_NODES

        wdc = self.wdc
        unk = self.unk
        fn = MakeLattice(nodes, self.set_mincost_node)
        for i in range(0, length):
            if nodes[i] is not None:
                fn.set(i)
                wdc.search(text, i, fn)  # 単語辞書から形態素を検索
                unk.search(text, i, wdc, fn)  # 未知語辞書から形態素を検索

        cur = self.set_mincost_node(ViterbiNode.makeBOSEOS(),
                                    nodes[length]).prev

        # reverse
        head = None
        while cur.prev:
            tmp = cur.prev
            cur.prev = head
            head = cur
            cur = tmp
        return head

    def set_mincost_node(self, vn, prevs):
        mtx = self.mtx
        left_id = vn.left_id
        f = vn.prev = prevs[0]
        mincost = f.cost + mtx.linkcost(f.right_id, left_id)

        for i in range(1, len(prevs)):
            p = prevs[i]
            cost = p.cost + mtx.linkcost(p.right_id, left_id)
            if cost < mincost:
                mincost = cost
                vn.prev = p

        vn.cost += mincost
        return vn

    def release(self):
        self.wdc.release()
        self.unk.release()
        self.mtx.release()

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        self.release()


class MakeLattice:
    __slots__ = ['nodes', 'i', 'prevs', 'empty', 'set_mincost_node']

    def __init__(self, nodes, set_mincost_node):
        self.nodes = nodes
        self.i = 0
        self.prevs = None
        self.empty = True
        self.set_mincost_node = set_mincost_node

    def set(self, i):
        self.i = i
        self.prevs = self.nodes[i]
        self.nodes[i] = None
        self.empty = True

    def __call__(self, vn):
        self.empty = False
        nodes = self.nodes
        end = self.i + vn.length
        if nodes[end] is None:
            nodes[end] = []
        ends = nodes[end]
        if vn.isspace:
            ends.extend(self.prevs)
        else:
            ends.append(self.set_mincost_node(vn, self.prevs))

    def isempty(self):
        return self.empty
