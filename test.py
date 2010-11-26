# coding: utf-8
import igo.Tagger

t = igo.Tagger.Tagger('../../ipadic', gae=True)
#t = igo.Tagger.Tagger('/mnt/dev/ipadic_gae', gae=True)
for m in t.parse(u'私の名前は中野です。'):
    print m.surface, m.feature, m.start
print
t = igo.Tagger.Tagger('/mnt/dev/ipadic')
for m in t.parse(u'こんにちは世界'):
    print m.surface, m.feature, m.start
