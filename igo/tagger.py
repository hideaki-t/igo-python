# -*- coding: utf-8 -*-
from igo.dictionary import Matrix, WordDic, Unknown, ViterbiNode
from igo.dictreader import UTF16Codec
import os.path
from os.path import dirname, abspath
import array


class Morpheme:
    """
    形態素クラス
    """

    def __init__(self, surface, feature, start):
        self.surface = surface
        """ 形態素の表層形 """
        self.feature = feature
        """ 形態素の素性 """
        self.start = start
        """ テキスト内での形態素の出現開始位置 """

    def __str__(self):
        return self.fmt()

    def fmt(self,
            fmt="surface: {surface}, feature: {feature}, start={start}"):
        return fmt.format(surface=self.surface,
                          feature=self.feature,
                          start=self.start)


class Tagger:
    """
    形態素解析を行うクラス
    """
    __BOS_NODES = [ViterbiNode.makeBOSEOS()]

    @staticmethod
    def lookup():
        """
        モジュールが置いてある場所から辞書を探す
        @return: モジュール内で見つかった辞書のパス
        """
        path = os.path.join(abspath(dirname(__file__)), 'dic')
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
        vn = self.__parseImpl(text)
        wordData = self.wdc.wordData
        while vn:
            surface = text[vn.start:vn.start + vn.length]
            feature = UTF16Codec.decode(wordData(vn.wordId))[0]
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
        vn = self.__parseImpl(text)
        while vn:
            result.append(text[vn.start:vn.start + vn.length])
            vn = vn.prev
        return result

    def __parseImpl(self, text):
        text = array.array('H', UTF16Codec.encode(text)[0])
        length = len(text)
        nodesAry = [None] * (length + 1)
        nodesAry[0] = Tagger.__BOS_NODES

        wdc = self.wdc
        unk = self.unk
        fn = MakeLattice(nodesAry, self.setMincostNode)
        for i in range(0, length):
            if nodesAry[i] is not None:
                fn.set(i)
                wdc.search(text, i, fn)       # 単語辞書から形態素を検索
                unk.search(text, i, wdc, fn)  # 未知語辞書から形態素を検索

        cur = self.setMincostNode(ViterbiNode.makeBOSEOS(),
                                  nodesAry[length]).prev

        # reverse
        head = None
        while cur.prev:
            tmp = cur.prev
            cur.prev = head
            head = cur
            cur = tmp
        return head

    def setMincostNode(self, vn, prevs):
        mtx = self.mtx
        leftId = vn.leftId
        f = vn.prev = prevs[0]
        minCost = f.cost + mtx.linkCost(f.rightId, leftId)

        for i in range(1, len(prevs)):
            p = prevs[i]
            cost = p.cost + mtx.linkCost(p.rightId, leftId)
            if cost < minCost:
                minCost = cost
                vn.prev = p

        vn.cost += minCost
        return vn


class MakeLattice:
    def __init__(self, nodesAry, setMincostNode):
        self.nodesAry = nodesAry
        self.i = 0
        self.prevs = None
        self.empty = True
        self.setMincostNode = setMincostNode

    def set(self, i):
        self.i = i
        self.prevs = self.nodesAry[i]
        self.nodesAry[i] = None
        self.empty = True

    def __call__(self, vn):
        self.empty = False
        nodesAry = self.nodesAry
        end = self.i + vn.length
        if nodesAry[end] is None:
            nodesAry[end] = []
        ends = nodesAry[end]
        if vn.isSpace:
            ends.extend(self.prevs)
        else:
            ends.append(self.setMincostNode(vn, self.prevs))

    def isEmpty(self):
        return self.empty
