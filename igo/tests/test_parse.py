# coding: utf-8
from __future__ import unicode_literals

import igo.tagger


def flat(m):
    return m.surface, m.feature, m.start


# t = igo.tagger.Tagger('ipadic_gae', gae=True)
def test_simple():
    t = igo.tagger.Tagger()
    a = [flat(x) for x in t.parse('こんにちは世界')]
    e = [('こんにちは', '感動詞,*,*,*,*,*,こんにちは,コンニチハ,コンニチワ', 0),
         ('世界', '名詞,一般,*,*,*,*,世界,セカイ,セカイ', 5)]
    assert a == e

    a = [flat(x) for x in t.parse('私の名前は中野です。')]
    e = [('私', '名詞,代名詞,一般,*,*,*,私,ワタシ,ワタシ', 0),
         ('の', '助詞,連体化,*,*,*,*,の,ノ,ノ', 1),
         ('名前', '名詞,一般,*,*,*,*,名前,ナマエ,ナマエ', 2),
         ('は', '助詞,係助詞,*,*,*,*,は,ハ,ワ', 4),
         ('中野', '名詞,固有名詞,地域,一般,*,*,中野,ナカノ,ナカノ', 5),
         ('です', '助動詞,*,*,*,特殊・デス,基本形,です,デス,デス', 7),
         ('。', '記号,句点,*,*,*,*,。,。,。', 9)]
    assert a == e


def test_surrogate_pairs():
    t = igo.tagger.Tagger()
    a = [flat(x) for x in t.parse('おはようー😳こんにちはー美味しいご飯だよ')]
    e = [('おはよう', '感動詞,*,*,*,*,*,おはよう,オハヨウ,オハヨー', 0),
         ('ー', '名詞,一般,*,*,*,*,*', 4), ('😳', '記号,一般,*,*,*,*,*', 5),
         ('こんにちは', '感動詞,*,*,*,*,*,こんにちは,コンニチハ,コンニチワ', 7),
         ('ー', '名詞,一般,*,*,*,*,*', 12),
         ('美味しい', '形容詞,自立,*,*,形容詞・イ段,基本形,美味しい,オイシイ,オイシイ', 13),
         ('ご飯', '名詞,一般,*,*,*,*,ご飯,ゴハン,ゴハン', 17),
         ('だ', '助動詞,*,*,*,特殊・ダ,基本形,だ,ダ,ダ', 19),
         ('よ', '助詞,終助詞,*,*,*,*,よ,ヨ,ヨ', 20)]
    assert a == e

    a = [flat(x) for x in t.parse('😳')]
    e = [('😳', '記号,一般,*,*,*,*,*', 0)]
    assert a == e

    a = [flat(x) for x in t.parse('😳😳')]
    e = [('😳😳', '記号,一般,*,*,*,*,*', 0)]
    assert a == e

    a = [flat(x) for x in t.parse('😳おはよう')]
    e = [('😳', '記号,一般,*,*,*,*,*', 0),
         ('おはよう', '感動詞,*,*,*,*,*,おはよう,オハヨウ,オハヨー', 2)]
    assert a == e

    a = [flat(x) for x in t.parse('おはよう😳')]
    e = [('おはよう', '感動詞,*,*,*,*,*,おはよう,オハヨウ,オハヨー', 0),
         ('😳', '記号,一般,*,*,*,*,*', 4)]
    assert a == e
