# coding: utf-8
import igo.tagger

t = igo.tagger.Tagger('ipadic_gae', gae=True)
for m in t.parse(u'私の名前は中野です。'):
    print m.surface, m.feature, m.start
print
t = igo.tagger.Tagger('ipadic')
for m in t.parse(u'こんにちは世界'):
    print m.surface, m.feature, m.start
print
t = igo.tagger.Tagger()
for m in t.parse(u'こんにちは世界'):
    print m.surface, m.feature, m.start
