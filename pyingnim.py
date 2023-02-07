import os
import sys
import requests
import argparse
import textwrap
from PIL import Image, ImageFilter, ImageDraw, ImageFont

VERSION             = "1.0"

LEFT_MARGIN         = 40
TAG_FONT_SIZE       = 18
TAG_IN_MARGIN       = 20
SMALL_IMAGE_OFFSET  = 72
DIAGONAL_JUMP       = 15

FONT_BOLD           = "resources/Lato-Bold.ttf"
FONT_REGULAR        = "resources/Lato-Regular.ttf"
TEMPLATE            = "resources/tmp.png"

def get_path(path) -> str:
    return os.path.join(os.path.dirname(__file__), path)

def get_bg(url) -> Image.Image:
    cover = Image.open(requests.get(url, stream=True).raw).convert("RGBA")
    # tmp = Image.new("RGBA", (1200, 630), (30, 30, 30, 245))
    tmp = Image.open(get_path(TEMPLATE))

    tw, th = tmp.size
    cw, ch = cover.size

    bw = int(tw * 0.8)
    br = bw / cw
    bh = int(br * ch)

    sr = th / ch
    sh = th
    sw = int(sr * cw)

    bc = cover.resize((bw, bh)).filter(ImageFilter.BoxBlur(3))
    sc = cover.resize((sw, sh))

    rw = SMALL_IMAGE_OFFSET
    for y in range(sh):
        for x in range(rw):
            sc.putpixel((x, y), (0, 0, 0, 0))
        if (y % DIAGONAL_JUMP == 0):
            rw = rw - 1

    csw = int(bw * 0.1)
    csh = int(bh * 0.1)
    bg = bc.crop((csw, csh, csw + tw, csh + th))

    bg.paste(sc, (tw - sw, 0), sc)
    bg.paste(tmp, (0, 0), tmp)
    return bg

def add_corners(im, rad) -> Image.Image:
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

def put_tags(image, tags) -> None:
    start = LEFT_MARGIN
    lato = ImageFont.FreeTypeFont(get_path(FONT_REGULAR), TAG_FONT_SIZE)
    for tag in tags:
        l = int(lato.getlength(tag))
        t = Image.new("RGBA", (l + (TAG_IN_MARGIN * 2), TAG_FONT_SIZE + TAG_IN_MARGIN), (40, 40, 40, 240))
        c = ImageDraw.Draw(t);
        c.text((TAG_IN_MARGIN, TAG_IN_MARGIN / 3), tag, fill = (235, 235, 235), font = lato)
        t = add_corners(t, 15)
        image.paste(t, (start, 550), t)
        start = start + l + 10 + (TAG_IN_MARGIN * 2)

def put_title(image, text) -> None:
    lato = ImageFont.FreeTypeFont(get_path(FONT_BOLD), 52)
    lines = textwrap.wrap(text, width = 26)
    # image.text((LEFT_MARGIN, 70), text, fill = (255, 255, 255), font = lato)
    image.text((LEFT_MARGIN, 70), '\n'.join(lines), fill = (255, 255, 255), font = lato)

def put_desc(image, text) -> None:
    lato = ImageFont.FreeTypeFont(get_path(FONT_REGULAR), 18)
    image.text((LEFT_MARGIN, 45), text, fill = (160, 160, 160), font = lato)

def put_mark(image, text) -> None:
    mark = ImageFont.FreeTypeFont(get_path(FONT_BOLD), 72)
    image.text((LEFT_MARGIN, 450), text, fill = (255, 0, 0), font = mark)

def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.usage = "pyingnim.py -u \"http://cdn.shinden.eu/cdn1/images/genuine/235677.jpg\" -o ../torr/img.png -t Gintama -d \"Lato 2020 / TV\" -r \"7.23\" --tags Horror Loli Dupa"
    parser.description = "Image generating script"
    parser.add_argument("-h", "--help", help="Show help", action="help")
    parser.add_argument("-v", "--version", help="Show version", action="version", version=VERSION)
    parser.add_argument("-t", help="Title", default=None)
    parser.add_argument("-d", help="Description", default=None)
    parser.add_argument("-r", help="Rating", default=None)
    parser.add_argument("-o", help="Output path", default=None)
    parser.add_argument("-u", help="Url to image", default=None)
    parser.add_argument("--tags", help="Tags divided by space", default=[], nargs='+')
    return parser

def main() -> None:
    parser = get_cli_parser()
    args = parser.parse_args()
    print("pyIngnim v" + VERSION)

    if args.u and args.o:
        bg = get_bg(args.u)

        if args.tags:
            put_tags(bg, args.tags)

        canvas = ImageDraw.Draw(bg);
        if args.t:
            put_title(canvas, args.t)
        if args.d:
            put_desc(canvas, args.d)
        if args.r:
            put_mark(canvas, args.r)

        bg.save(args.o)
        sys.exit(0)

    parser.print_usage()
    sys.exit(1)

if __name__ == '__main__':
    main()