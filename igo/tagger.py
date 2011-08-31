# -*- coding: utf-8 -*-
from igo.dictionary import Matrix, WordDic, Unknown, ViterbiNode
import os.path
from os.path import dirname, abspath
import sys


if sys.version_info[0] > 2:
    unichr = chr
    empty = ""
else:
    empty = unicode('')


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

    def __init__(self, dataDir=None, gae=False):
        """
        バイナリ辞書を読み込んで、形態素解析器のインスタンスを作成する

        @param dataDir バイナリ辞書があるディレクトリ
        @throws FileNotFoundException 間f違ったディレクトリが指定された場合に送出される
        @throws IOException その他の入出力エラーが発生した場合に送出される
        """
        if not dataDir:
            dataDir = Tagger.lookup()
        self.wdc = WordDic(dataDir, gae, gae)
        self.unk = Unknown(dataDir, gae)
        self.mtx = Matrix(dataDir, gae)

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
            feature = ''.join([unichr(x) for x in wordData(vn.wordId)])
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
        length = len(text)
        nodesAry = []
        nodesAry.append(Tagger.__BOS_NODES)
        for i in range(0, length):
            nodesAry.append([])

        wdc = self.wdc
        unk = self.unk
        fn = MakeLattice(nodesAry, self.setMincostNode)
        for i in range(0, length):
            if len(nodesAry[i]):
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
        self.empty = True

    def __call__(self, vn):
        self.empty = False
        t = self.nodesAry[self.i + vn.length]
        if vn.isSpace:
            t.extend(self.prevs)
        else:
            t.append(self.setMincostNode(vn, self.prevs))

    def isEmpty(self):
        return self.empty
