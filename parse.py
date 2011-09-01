import sys
import igo


if sys.version_info[0] < 3:
    u = lambda s: s.decode('utf-8')
    import codecs
    sys.stdout = codecs.lookup('utf-8').streamwriter(sys.stdout)
    sys.stdin = codecs.lookup('utf-8').streamreader(sys.stdin)
else:
    import io
    u = str
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def pp(sf, ft, st):
    sys.stdout.write(u("%s\t%s\n") % (sf, ft))


tagger = igo.tagger.Tagger('ipadic')

for l in sys.stdin:
    for m in tagger.parse(l):
        pp(m.surface, m.feature, m.start)
