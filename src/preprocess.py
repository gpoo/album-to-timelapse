#!/usr/bin/env python3

import sys
import argparse
from os import listdir
from os.path import isfile, isdir, join, basename

from wand.image import Image
from wand.display import display
from wand.color import Color

name = 'foo - Convert pictures to full HD image size'


def get_metadata(f):
    ORIENTATION = 'exif:Orientation'
    WIDTH = 'exif:ExifImageWidth'
    HEIGHT = 'exif:ExifImageLength'
    with Image(filename=f) as i:
        w = int(i.metadata[WIDTH]) if WIDTH in i.metadata else -1
        h = int(i.metadata[HEIGHT]) if HEIGHT in i.metadata else -1
        d = i.metadata['exif:DateTime']
        o = int(i.metadata[ORIENTATION]) if ORIENTATION in i.metadata else -1
        m = i.metadata['exif:Make']

        if m == 'LGE':
            orientation = 'Portrait' if h > w else 'Landscape'
        elif m == 'FUJIFILM':
            orientation = 'Portrait' if o in (6, 8) else 'Landscape'
        return w, h, o, d, m, orientation

def process_fujifilm(f, w, h, o, d, m, o2):
    black = Color('black')
    width = 1920
    height = 1080

    with Image(filename=f) as img:
        if o == 8 and h < w:
            img.rotate(-90, background=black)
        elif o == 6 and h < w:
            img.rotate(90, background=black)
        elif o == 3:
            img.rotate(180, background=black)
        img.transform(resize='{}x{}'.format(width, height))
        with Image(width=width, height=height, background=black) as out:
            out.format = img.format.lower()
            out.composite(img, left=int((width - img.width)/ 2),
                          top=int((height - img.height) / 2))
            display(out)


def process_lge(f, w, h, o, d, m, o2):
    black = Color('black')
    width = 1920
    height = 1080
    with Image(filename=f) as img:
        img.transform(resize='{}x{}'.format(width, height))
        with Image(width=width, height=height, background=black) as out:
            out.format = img.format.lower()
            out.composite(img, left=int((width - img.width)/ 2),
                          top=int((height - img.height) / 2))
            display(out)


def process(f, w, h, o, d, m, o2):
    if m == 'FUJIFILM':
        process_fujifilm(f, w, h, o, d, m, o2)
    elif m == 'LGE':
        process_lge(f, w, h, o, d, m, o2)
    else:
        print('Unknown camera {}'.format(m))


def main(args):
    files = []
    for i in args:
        if isdir(i):
            files.extend([join(i, f) for f in listdir(i)
                         if isfile(join(i, f)) and f.endswith('.jpg')])
        else:
            files.append(i)

    for i in sorted(files):
        print(basename(i), end=': ')
        w, h, o, d, m, o2 = get_metadata(i)
        print('{}x{} {} {} {} {}'.format(w, h, o, d, m, o2))
        process(i, w, h, o, d, m, o2)


def start():
    args = argparse.ArgumentParser(description=name)

    args.add_argument('source', nargs='+',
                      help='Source directory')

    opts = args.parse_args()

    if '-' in opts.source:
        sources = [s.strip() for s in sys.stdin.readlines()]
    else:
        sources = opts.source

    main(sources)

if __name__ == '__main__':
    start()
