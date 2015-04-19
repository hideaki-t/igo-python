from __future__ import unicode_literals, print_function
import sys
from .tagger import Tagger


def main():
    if sys.version_info[0] < 3 and sys.platform != 'cli':
        import codecs
        i = codecs.lookup(sys.getfilesystemencoding()).streamreader(sys.stdin)
    else:
        i = sys.stdin

    with Tagger('ipadic') as tagger:
        for l in i:
            for m in tagger.parse(l):
                print(m.fmt('{surface}\t{feature}'))
            print('EOS')

if __name__ == '__main__':
    main()
