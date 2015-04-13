from __future__ import unicode_literals, print_function
import sys
import igo


def pp(sf, ft, st, o=sys.stdout):
    print("%s\t%s" % (sf, ft))

if sys.version_info[0] < 3 and sys.platform != 'cli':
    import codecs
    i = codecs.lookup(sys.getfilesystemencoding()).streamreader(sys.stdin)
else:
    i = sys.stdin

tagger = igo.tagger.Tagger('ipadic')

for l in i:
    for m in tagger.parse(l):
        pp(m.surface, m.feature, m.start)
