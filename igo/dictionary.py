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
    __slots__ = ['cost', 'prev', 'word_id', 'start', 'length', 'left_id',
                 'right_id', 'isspace']

    def __init__(self, word_id, start, length, cost, left_id, right_id,
                 isspace):
        self.cost = cost
        """ 始点からノードまでの総コスト """
        self.prev = None
        """ コスト最小の前方のノードへのリンク """
        self.word_id = word_id
        """ 単語ID """
        self.start = start
        """ 入力テキスト内での形態素の開始位置 """
        self.length = length
        """ 形態素の表層形の長さ(文字数) """
        self.left_id = left_id
        """ 左文脈ID """
        self.right_id = right_id
        """ 右文脈ID """
        self.isspace = isspace
        """ 形態素の文字種(文字カテゴリ)が空白文字かどうか """

    @staticmethod
    def makeBOSEOS():
        return ViterbiNode(0, 0, 0, 0, 0, 0, False)

    def __repr__(self):
        return str({n: getattr(self, n) for n in ViterbiNode.__slots__})


class CharCategory:
    __slots__ = ['cc_rd', 'cat', 'c2c_rd', 'char2id', 'eql_masks']

    def __init__(self, path, bigendian=False, use_mmap=None):
        self.cc_rd = DictReader(path + "/char.category", bigendian, use_mmap)
        with self.cc_rd as r:
            self.cat = self.convert_categories(r.get_intarray())
        self.c2c_rd = DictReader(path + "/code2category", bigendian, use_mmap)
        with self.c2c_rd as r:
            self.char2id = r.get_intarray(r.size() // 4 // 2)
            self.eql_masks = r.get_intarray(r.size() // 4 // 2)

    def release(self):
        del self.cat
        del self.char2id
        del self.eql_masks
        self.cc_rd.release()
        del self.cc_rd
        self.c2c_rd.release()
        del self.c2c_rd

    def category(self, code):
        return self.cat[self.char2id[code]]

    def is_compatible(self, code1, code2):
        return (self.eql_masks[code1] & self.eql_masks[code2]) != 0

    def convert_categories(self, d):
        return [
            Category(d[i], d[i + 1], d[i + 2], d[i + 3])
            for i in range(0, len(d), 4)
        ]


class Category:
    __slots__ = ['id', 'length', 'invoke', 'group']

    def __init__(self, i, l, iv, g):
        self.id = i
        self.length = l
        self.invoke = iv == 1
        self.group = g == 1


class Matrix:
    """
    形態素の連接コスト表を扱うクラス
    """
    __slots__ = ['rd', 'left_size', 'matrix']

    def __init__(self, path, bigendian=False, use_mmap=None):
        self.rd = DictReader(path + "/matrix.bin", bigendian, use_mmap)
        with self.rd as r:
            self.left_size = r.get_int()
            right_size = r.get_int()
            self.matrix = r.get_shortarray(self.left_size * right_size)

    def release(self):
        del self.matrix
        self.rd.release()

    def linkcost(self, left_id, right_id):
        """
        形態素同士の連接コストを求める
        """
        return self.matrix[right_id * self.left_size + left_id]


class Unknown:
    """
    未知語の検索を行うクラス
    """
    __slots__ = ['category', 'space_id']

    def __init__(self, path, bigendian=False, use_mmap=None):
        self.category = CharCategory(path, bigendian, use_mmap)
        """文字カテゴリ管理クラス"""
        # NOTE: ' 'の文字カテゴリはSPACEに予約されている
        self.space_id = self.category.category(0x20).id
        """文字カテゴリがSPACEの文字のID"""

    def release(self):
        self.category.release()

    def search(self, text, start, wdic, callback):
        category = self.category
        ch = text[start]
        ct = category.category(ch)
        length = len(text)

        if not callback.isempty() and not ct.invoke:
            return

        cid = ct.id
        isspace = cid == self.space_id
        limit = min(length, ct.length + start)
        for i in range(start + 1, limit):
            wdic.search_from_trie(cid, start, i - start, isspace, callback)
            if not category.is_compatible(ch, text[i]):
                return
        wdic.search_from_trie(cid, start, limit - start, isspace, callback)

        if ct.group and limit < length:
            for i in range(limit, length):
                if not category.is_compatible(ch, text[i]):
                    wdic.search_from_trie(cid, start, i - start, isspace,
                                          callback)
                    return
            wdic.search_from_trie(cid, start, length - start, isspace,
                                  callback)


class WordDic:
    __slots__ = ['splitted', 'trie', 'data', 'wd_rd', 'wa_rd', 'indices',
                 'wi_rd', 'offsets', 'left_ids', 'right_ids', 'costs']

    def __init__(self, path, bigendian=False, splitted=False, use_mmap=None):
        self.splitted = splitted
        self.trie = Searcher(path + "/word2id", bigendian, use_mmap)
        if splitted:
            paths = sorted(glob.glob(path + "/word.dat.*"))
            self.data = util.get_chararray_multi(paths, bigendian)
        else:
            self.wd_rd = DictReader(path + "/word.dat", bigendian, use_mmap)
            with self.wd_rd as r:
                self.data = r.get_chararray()
        self.wa_rd = DictReader(path + "/word.ary.idx", bigendian, use_mmap)
        with self.wa_rd as r:
            self.indices = r.get_intarray()
        self.wi_rd = DictReader(path + "/word.inf", bigendian, use_mmap)
        with self.wi_rd as r:
            wc = r.size() // (4 + 2 + 2 + 2)
            self.offsets = r.get_intarray(wc)
            """ dataOffsets[単語ID] = 単語の素性データの開始位置 """
            self.left_ids = r.get_shortarray(wc)
            """ leftIds[単語ID] = 単語の左文脈ID """
            self.right_ids = r.get_shortarray(wc)
            """ rightIds[単語ID] = 単語の右文脈ID """
            self.costs = r.get_shortarray(wc)
            """ consts[単語ID] = 単語のコスト """

    def release(self):
        del self.data
        del self.indices
        del self.offsets
        del self.left_ids
        del self.right_ids
        del self.costs
        self.trie.release()
        del self.trie
        if not self.splitted:
            self.wd_rd.release()
            del self.wd_rd
        self.wa_rd.release()
        del self.wa_rd
        self.wi_rd.release()
        del self.wi_rd

    def search(self, text, start, callback):
        costs = self.costs
        left_ids = self.left_ids
        right_ids = self.right_ids
        indices = self.indices

        def fn(start, offset, trieId):
            end = indices[trieId + 1]
            for i in range(indices[trieId], end):
                callback(ViterbiNode(i, start, offset, costs[i], left_ids[i],
                                     right_ids[i], False))

        self.trie.commonprefix_search(text, start, fn)

    def search_from_trie(self, trie_id, start, length, isspace, callback):
        costs = self.costs
        left_ids = self.left_ids
        right_ids = self.right_ids
        end = self.indices[trie_id + 1]
        for i in range(self.indices[trie_id], end):
            callback(ViterbiNode(i, start, length, costs[i], left_ids[i],
                                 right_ids[i], isspace))

    def word_data(self, word_id):
        return tobytes(self.data[self.offsets[word_id]:self.offsets[word_id +
                                                                    1]])
