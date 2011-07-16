# -*- coding: utf-8 -*-
from igo.dictionary import Matrix, WordDic, Unknown, ViterbiNode


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

    def __init__(self, dataDir, gae=False):
        """
        バイナリ辞書を読み込んで、形態素解析器のインスタンスを作成する

        @param dataDir バイナリ辞書があるディレクトリ
        @throws FileNotFoundException 間f違ったディレクトリが指定された場合に送出される
        @throws IOException その他の入出力エラーが発生した場合に送出される
        """
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
        while vn:
            surface = text[vn.start:vn.start + vn.length]
            feature = u''.join([unichr(x) for x in self.wdc.wordData(vn.wordId)])
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
        for i in range(0, length):
            perResult = []
            if len(nodesAry[i]):
                self.wdc.search(text, i, perResult)       # 単語辞書から形態素を検索
                self.unk.search(text, i, self.wdc, perResult)  # 未知語辞書から形態素を検索
                prevs = nodesAry[i]
                for j in range(0, len(perResult)):
                    vn = perResult[j]
                    if vn.isSpace:
                        (nodesAry[i + vn.length]).extend(prevs)
                    else:
                        (nodesAry[i + vn.length]).append(self.setMincostNode(vn, prevs))
        cur = self.setMincostNode(ViterbiNode.makeBOSEOS(), nodesAry[length]).prev

        # reverse
        head = None
        while cur.prev:
            tmp = cur.prev
            cur.prev = head
            head = cur
            cur = tmp
        return head

    def setMincostNode(self, vn, prevs):
        f = vn.prev = prevs[0]
        vn.cost = f.cost + self.mtx.linkCost(f.rightId, vn.leftId)

        for i in range(1, len(prevs)):
            p = prevs[i]
            cost = p.cost + self.mtx.linkCost(p.rightId, vn.leftId)
            if cost < vn.cost:
                vn.cost = cost
                vn.prev = p

        vn.cost += self.wdc.cost(vn.wordId)
        return vn
