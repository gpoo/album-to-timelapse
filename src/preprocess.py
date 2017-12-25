#!/usr/bin/env python3

import sys
import argparse
import logging
from os import listdir
from os.path import isfile, isdir, join, basename
from datetime import datetime

from wand.image import Image
from wand.display import display
from wand.color import Color

name = 'foo - Convert pictures to full HD image size'

def get_metadata(f):
    ORIENTATION = 'exif:Orientation'
    WIDTH = 'exif:ExifImageWidth'
    HEIGHT = 'exif:ExifImageLength'
    DATE = 'exif:DateTimeOriginal'
    with Image(filename=f) as i:
        w = int(i.metadata[WIDTH]) if WIDTH in i.metadata else -1
        h = int(i.metadata[HEIGHT]) if HEIGHT in i.metadata else -1
        d = i.metadata[DATE] if DATE in i.metadata else -1
        o = int(i.metadata[ORIENTATION]) if ORIENTATION in i.metadata else -1
        m = i.metadata['exif:Make']

        if m in ('FUJIFILM', 'NIKON CORPORATION', 'Canon', 'samsung'):
            orientation = 'Portrait' if o in (6, 8) else 'Landscape'
        else:
            orientation = 'Portrait' if h > w else 'Landscape'

        return w, h, o, d, m, orientation

def process_fujifilm(img, w, h, o):
    if o == 8 and h < w:
        img.rotate(-90)
    elif o == 6 and h < w:
        img.rotate(90)
    elif o == 3:
        img.rotate(180)

    return img


def process_lge(img, w, h, o):
    return img


def process(f, w, h, o, d, m, o2, output):
    black = Color('black')
    width = 1920
    height = 1080

    with Image(filename=f) as f:
        if m in ('FUJIFILM', 'NIKON CORPORATION', 'Canon', 'samsung'):
            img = process_fujifilm(f, w, h, o)
        elif m == 'LGE':
            img = process_lge(f, w, h, o)
        else:
            logging.warning('Unknown camera {}'.format(m))
            img = f

        img.transform(resize='{}x{}'.format(width, height))

        with Image(width=width, height=height, background=black) as out:
            out.format = img.format.lower()
            out.composite(img, left=int((width - img.width)/ 2),
                          top=int((height - img.height) / 2))
            logging.info(output)
            out.save(filename=output)

def main(args, dstdir):
    dt_from_filter = datetime.strptime('2016:12:24 0:0:0',
                                       '%Y:%m:%d %H:%M:%S')
    files = []
    for i in args:
        if isdir(i):
            files.extend([join(i, f) for f in listdir(i)
                         if isfile(join(i, f)) and f.endswith('.jpg')])
        else:
            files.append(i)

    for i in sorted(files):
        w, h, o, d, m, o2 = get_metadata(i)
        logging.info('{} {}x{} {} {} {} {}'.format(basename(i),
                                                   w, h, o, d, m, o2))
        dt = datetime.strptime(d, '%Y:%m:%d %H:%M:%S')
        if dt >= dt_from_filter:
            output = join(dstdir, dt.strftime('%Y%m%d-%H%M%S.jpg'))
            process(i, w, h, o, dt, m, o2, output)

def start():

    args = argparse.ArgumentParser(description=name)

    args.add_argument('source', nargs='+',
                      help='Source directory')
    args.add_argument('--output', default='/tmp',
                      help='Directory to save the resulting images')

    opts = args.parse_args()

    if '-' in opts.source:
        sources = [s.strip() for s in sys.stdin.readlines()]
    else:
        sources = opts.source
    dstdir = opts.output

    main(sources, dstdir)

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s')
    start()
