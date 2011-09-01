import lxml.html
import sys


if sys.version_info[0] < 3:
    import codecs
    sys.stdout = codecs.lookup('utf-8').streamwriter(sys.stdout)
else:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


target = sys.argv[1] if len(sys.argv) > 1 else sys.stdin
r = lxml.html.parse(target).getroot()
print(r.text_content())
