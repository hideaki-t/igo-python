# -*- coding: utf-8 -*-
from __future__ import division
import glob
import sys
import igo.dictreader as util
from igo.dictreader import DictReader
from igo.trie import Searcher

if sys.version_info[0] > 2:
    def tobytes(x):
        return x.tobytes()
else:
    def tobytes(x):
        return x.tostring()


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
    def __init__(self, path, bigendian=False, use_mmap=None):
        self.cat = CharCategory.readCategories(path, bigendian, use_mmap)
        with DictReader(path + "/code2category", bigendian, use_mmap) as r:
            self.char2id = r.getIntArray(r.size() // 4 // 2)
            self.eqlMasks = r.getIntArray(r.size() // 4 // 2)

    def category(self, code):
        return self.cat[self.char2id[code]]

    def isCompatible(self, code1, code2):
        return (self.eqlMasks[code1] & self.eqlMasks[code2]) != 0

    @staticmethod
    def readCategories(path, bigendian, use_mmap):
        with DictReader(path + "/char.category", bigendian, use_mmap) as r:
            data = r.getIntArray()
        size = len(data)
        l = []
        for i in range(0, size, 4):
            l.append(Category(data[i], data[i + 1],
                              data[i + 2] == 1, data[i + 3] == 1))
        return l


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
    def __init__(self, path, bigendian=False, use_mmap=None):
        with DictReader(path + "/matrix.bin", bigendian, use_mmap) as r:
            self.leftSize = r.getInt()
            self.rightSize = r.getInt()
            self.matrix = r.getShortArray(self.leftSize * self.rightSize)

    def linkCost(self, leftId, rightId):
        """
        形態素同士の連接コストを求める
        """
        return self.matrix[rightId * self.leftSize + leftId]


class Unknown:
    """
    未知語の検索を行うクラス
    """
    def __init__(self, path, bigendian=False, use_mmap=None):
        self.category = CharCategory(path, bigendian, use_mmap)
        """文字カテゴリ管理クラス"""
        # NOTE: ' 'の文字カテゴリはSPACEに予約されている
        self.spaceId = self.category.category(0x20).id
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
    def __init__(self, path, bigendian=False, splitted=False, use_mmap=None):
        self.trie = Searcher(path + "/word2id", bigendian, use_mmap)
        if splitted:
            paths = sorted(glob.glob(path + "/word.dat.*"))
            self.data = util.getCharArrayMulti(paths, bigendian)
        else:
            with DictReader(path + "/word.dat", bigendian, use_mmap) as r:
                self.data = r.getCharArray()
        with DictReader(path + "/word.ary.idx", bigendian, use_mmap) as r:
            self.indices = r.getIntArray()

        with DictReader(path + "/word.inf", bigendian, use_mmap) as r:
            wordCount = r.size() // (4 + 2 + 2 + 2)
            self.dataOffsets = r.getIntArray(wordCount)
            """ dataOffsets[単語ID] = 単語の素性データの開始位置 """
            self.leftIds = r.getShortArray(wordCount)
            """ leftIds[単語ID] = 単語の左文脈ID """
            self.rightIds = r.getShortArray(wordCount)
            """ rightIds[単語ID] = 単語の右文脈ID """
            self.costs = r.getShortArray(wordCount)
            """ consts[単語ID] = 単語のコスト """

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
        return tobytes(
            self.data[self.dataOffsets[wordId]:self.dataOffsets[wordId + 1]])
