from __future__ import unicode_literals, print_function
import sys
import locale
import io
import os
from .tagger import Tagger


def main():
    if sys.platform == 'cli':
        i = sys.stdin
        o = sys.stdout
    elif sys.version_info[0] < 3:
        enc = locale.getpreferredencoding()
        i = io.open(sys.stdin.fileno(), encoding=enc, closefd=False)
        o = io.open(sys.stdout.fileno(), mode='w', encoding=enc, closefd=False)
    else:
        # just turn on universal newline mode to align python2
        i = io.TextIOWrapper(sys.stdin.buffer)
        o = sys.stdout

    with Tagger(os.getenv('IGO_DICT')) as tagger:
        for l in i:
            for m in tagger.parse(l):
                print(m.fmt('{surface}\t{feature}'), file=o)
            print('EOS', file=o)

if __name__ == '__main__':
    main()
