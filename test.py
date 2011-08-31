# coding: utf-8
import os
import sys
import igo.tagger


if sys.version_info[0] < 3:
    u = lambda s: s.decode('utf-8')
    import codecs
    sys.stdout = codecs.lookup('utf-8').streamwriter(sys.stdout)
else:
    u = str


def pp(sf, ft, st):
    sys.stdout.write(u("%s: %s at %d\n") % (sf, ft, st))


t = igo.tagger.Tagger('ipadic_gae', gae=True)
for m in t.parse(u('私の名前は中野です。')):
    pp(m.surface, m.feature, m.start)
print('\n')

t = igo.tagger.Tagger('ipadic')
for m in t.parse(u('こんにちは世界')):
    pp(m.surface, m.feature, m.start)
print('\n')

# test if the dictionary exists
try:
    os.symlink(os.path.join(os.getcwd(), 'ipadic'), 'igo/dic')
    if os.path.exists('igo/dic'):
        t = igo.tagger.Tagger()
        for m in t.parse(u('こんにちは世界')):
            pp(m.surface, m.feature, m.start)
        print('\n')
    os.remove('igo/dic')
except:
    pass
