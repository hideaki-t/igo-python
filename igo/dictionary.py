# -*- coding: utf-8 -*-
from __future__ import division
import glob
import sys
import igo.util as util
from igo.util import FileMappedInputStream
from igo.trie import Searcher


if sys.version_info[0] > 2:
    space = ' '
else:
    space = unichr(0x20)


class ViterbiNode(object):
    """
    Viterbiアルゴリズムで使用されるノード
    """
    def __init__(self, wordId, start, length, cost, leftId, rightId, isSpace):
        self.cost = cost
        """ 始点からノードまでの総コスト """
        self.prev = None
        """ コスト最小の前方のノードへのリンク """
        self.wordId = wordId
        """ 単語ID """
        self.start = start
        """ 入力テキスト内での形態素の開始位置 """
        self.length = length
        """ 形態素の表層形の長さ(文字数) """
        self.leftId = leftId
        """ 左文脈ID """
        self.rightId = rightId
        """ 右文脈ID """
        self.isSpace = isSpace
        """ 形態素の文字種(文字カテゴリ)が空白文字かどうか """

    @staticmethod
    def makeBOSEOS():
        return ViterbiNode(0, 0, 0, 0, 0, 0, False)


class CharCategory:
    def __init__(self, dataDir, bigendian=False):
        self.categorys = CharCategory.readCategorys(dataDir, bigendian)
        fmis = FileMappedInputStream(dataDir + "/code2category", bigendian)
        try:
            self.char2id = fmis.getIntArray(fmis.size() // 4 // 2)
            self.eqlMasks = fmis.getIntArray(fmis.size() // 4 // 2)
        finally:
            fmis.close()

    def category(self, code):
        return self.categorys[self.char2id[ord(code)]]

    def isCompatible(self, code1, code2):
        return (self.eqlMasks[ord(code1)] & self.eqlMasks[ord(code2)]) != 0

    @staticmethod
    def readCategorys(dataDir, bigendian):
        data = util.getIntArray(dataDir + "/char.category", bigendian)
        size = len(data) // 4
        ary = []
        for i in range(0, size):
            ary.append(Category(data[i * 4], data[i * 4 + 1],
                                data[i * 4 + 2] == 1, data[i * 4 + 3] == 1))
        return ary


class Category:
    def __init__(self, i, l, iv, g):
        self.id = i
        self.length = l
        self.invoke = iv
        self.group = g


class Matrix:
    """
    形態素の連接コスト表を扱うクラス
    """
    def __init__(self, dataDir, bigendian=False):
        fmis = FileMappedInputStream(dataDir + "/matrix.bin", bigendian)
        try:
            self.leftSize = fmis.getInt()
            self.rightSize = fmis.getInt()
            self.matrix = fmis.getShortArray(self.leftSize * self.rightSize)
        finally:
            fmis.close()

    def linkCost(self, leftId, rightId):
        """
        形態素同士の連接コストを求める
        """
        return self.matrix[rightId * self.rightSize + leftId]


class Unknown:
    """
    未知語の検索を行うクラス
    """
    def __init__(self, dataDir, bigendian=False):
        self.category = CharCategory(dataDir, bigendian)
        """文字カテゴリ管理クラス"""
        # NOTE: ' 'の文字カテゴリはSPACEに予約されている
        self.spaceId = self.category.category(space).id
        """文字カテゴリがSPACEの文字のID"""

    def search(self, text, start, wdic, callback):
        category = self.category
        ch = text[start]
        ct = category.category(ch)
        length = len(text)

        if not callback.isEmpty() and not ct.invoke:
            return

        isSpace = ct.id == self.spaceId
        limit = min(length, ct.length + start)
        for i in range(start, limit):
            wdic.searchFromTrieId(ct.id, start,
                                  (i - start) + 1, isSpace, callback)
            if i + 1 != limit and not category.isCompatible(ch, text[i + 1]):
                return

        if ct.group and limit < length:
            for i in range(limit, length):
                if not category.isCompatible(ch, text[i]):
                    wdic.searchFromTrieId(ct.id, start,
                                          i - start, isSpace, callback)
                    return
            wdic.searchFromTrieId(ct.id, start,
                                  length - start, isSpace, callback)


class WordDic:
    def __init__(self, dataDir, bigendian=False, splitted=False):
        self.trie = Searcher(dataDir + "/word2id", bigendian)
        if splitted:
            paths = sorted(glob.glob(dataDir + "/word.dat.*"))
            self.data = util.getCharArrayMulti(paths, bigendian)
        else:
            self.data = util.getCharArray(dataDir + "/word.dat", bigendian)
        self.indices = util.getIntArray(dataDir + "/word.ary.idx", bigendian)

        fmis = FileMappedInputStream(dataDir + "/word.inf", bigendian)
        try:
            wordCount = fmis.size() // (4 + 2 + 2 + 2)
            self.dataOffsets = fmis.getIntArray(wordCount)
            """ dataOffsets[単語ID] = 単語の素性データの開始位置 """
            self.leftIds = fmis.getShortArray(wordCount)
            """ leftIds[単語ID] = 単語の左文脈ID """
            self.rightIds = fmis.getShortArray(wordCount)
            """ rightIds[単語ID] = 単語の右文脈ID """
            self.costs = fmis.getShortArray(wordCount)
            """ consts[単語ID] = 単語のコスト """
        finally:
            fmis.close()

    def search(self, text, start, callback):
        costs = self.costs
        leftIds = self.leftIds
        rightIds = self.rightIds
        indices = self.indices

        def fn(start, offset, trieId):
            end = indices[trieId + 1]
            for i in range(indices[trieId], end):
                callback(ViterbiNode(i, start, offset, costs[i],
                                     leftIds[i], rightIds[i], False))

        self.trie.eachCommonPrefix(text, start, fn)

    def searchFromTrieId(self, trieId, start, wordLength, isSpace, callback):
        costs = self.costs
        leftIds = self.leftIds
        rightIds = self.rightIds
        end = self.indices[trieId + 1]
        for i in range(self.indices[trieId], end):
            callback(ViterbiNode(i, start, wordLength, costs[i],
                                 leftIds[i], rightIds[i], isSpace))

    def wordData(self, wordId):
        return self.data[self.dataOffsets[wordId]:self.dataOffsets[wordId + 1]]
