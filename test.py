# coding: utf-8
import igo.Tagger

t = igo.Tagger.Tagger('/mnt/dev/ipadic')
l = t.parse(u'こんにちは世界')
for m in l:
	print m.surface, m.feature, m.start
