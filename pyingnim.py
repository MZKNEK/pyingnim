import os
import sys
import requests
import argparse
import textwrap
from PIL import Image, ImageFilter, ImageDraw, ImageFont

VERSION = "1.4"

# FOR TEMPLATE 1200x630
MIN_COVER_WIDTH = 446
TITLE_FONT_SIZE = 62
DESC_FONT_SIZE  = 23
LEFT_MARGIN     = 50
TAG_FONT_SIZE   = 20
TAG_IN_MARGIN   = 20
TAG_SPACING     = 10
RATE_FONT_SIZE  = 72
DIAGONAL_JUMP   = 15

FONT_BOLD       = "resources/Lato-Bold.ttf"
FONT_REGULAR    = "resources/Lato-Regular.ttf"
TEMPLATE        = "resources/tmp.png"
STAR            = "resources/star.png"


def get_path(path) -> str:
    return os.path.join(os.path.dirname(__file__), path)


def get_cover(url, path) -> Image.Image:
    if url:
        return Image.open(requests.get(url, stream=True).raw).convert("RGBA")
    if path:
        return Image.open(path).convert("RGBA")
    return None


def get_bg(cover) -> Image.Image:
    tmp = Image.open(get_path(TEMPLATE))

    tw, th = tmp.size
    cw, ch = cover.size

    bw = int(tw * 0.8)
    br = bw / cw
    bh = int(br * ch)

    sr = th / ch
    sh = th
    sw = int(sr * cw)

    if sw < MIN_COVER_WIDTH:
        sw = MIN_COVER_WIDTH
        sr = sw / cw
        sh = int(sr * ch)

    bc = cover.resize((bw, bh)).filter(ImageFilter.BoxBlur(3))
    sc = cover.resize((sw, sh))

    rw = sw - 386
    for y in range(sh):
        for x in range(rw):
            sc.putpixel((x, y), (0, 0, 0, 0))
        if (y % DIAGONAL_JUMP == 0):
            rw -= 1

    csw = int(bw * 0.1)
    csh = int(bh * 0.1)
    bg = bc.crop((csw, csh, csw + tw, csh + th))

    bg.paste(sc, (tw - sw, 0), sc)
    return Image.alpha_composite(bg, tmp)


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


def get_real_tags(font, tags, maxSize) -> list[str]:
    newTags = []
    totalLen = 0
    for tag in tags:
        tLen = font.getlength(tag)
        tLen += TAG_SPACING + (TAG_IN_MARGIN * 2)
        if totalLen + tLen <= maxSize:
            newTags.append(tag)
            totalLen += tLen
        else:
            break
    return newTags


def put_tags(image, tags) -> None:
    start = LEFT_MARGIN
    font = ImageFont.FreeTypeFont(get_path(FONT_REGULAR), TAG_FONT_SIZE)
    for tag in get_real_tags(font, tags, 700):
        ln = int(font.getlength(tag))
        tImg = Image.new("RGBA", (ln + (TAG_IN_MARGIN * 2),
                         TAG_FONT_SIZE + TAG_IN_MARGIN), (40, 40, 40, 240))
        canvas = ImageDraw.Draw(tImg)
        canvas.text((TAG_IN_MARGIN, TAG_IN_MARGIN / 3),
                    tag, fill=(235, 235, 235), font=font)
        tImg = add_corners(tImg, 15)
        image.paste(tImg, (start, 550), tImg)
        start += ln + TAG_SPACING + (TAG_IN_MARGIN * 2)


def get_max_len(font, size, max=40) -> int:
    for i in range(max):
        l = int(font.getlength(('g' * i)))
        if l > size:
            return i
    return max


def put_title(canvas, text) -> None:
    fontSize = TITLE_FONT_SIZE
    textSize = len(text)
    if textSize > 90:
        fontSize = fontSize - (10 * int(textSize / 70))

    font = ImageFont.FreeTypeFont(get_path(FONT_BOLD), fontSize)
    lines = textwrap.wrap(text, width=get_max_len(font, 760))
    canvas.text((LEFT_MARGIN, 75), '\n'.join(
        lines), fill=(255, 255, 255), font=font)


def put_desc(canvas, text) -> None:
    font = ImageFont.FreeTypeFont(get_path(FONT_REGULAR), DESC_FONT_SIZE)
    canvas.text((LEFT_MARGIN, 37), text, fill=(160, 160, 160), font=font)


def put_mark(image, canvas, text) -> None:
    star = Image.open(get_path(STAR)).resize((RATE_FONT_SIZE, RATE_FONT_SIZE))
    image.paste(star, (LEFT_MARGIN, 458), star)

    font = ImageFont.FreeTypeFont(get_path(FONT_BOLD), RATE_FONT_SIZE)
    canvas.text(
        (LEFT_MARGIN + 10 + star.size[0], 450), text, fill=(255, 255, 255), font=font)


def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.description = "Image generating script"
    parser.add_argument("-h", "--help", help="Show help", action="help")
    parser.add_argument("-v", "--version", help="Show version",
                        action="version", version=VERSION)
    parser.add_argument("-t", help="Title", default=None)
    parser.add_argument("-d", help="Description", default=None)
    parser.add_argument("-r", help="Rating", default=None)
    parser.add_argument("-o", help="Output path", default=None)
    parser.add_argument("-u", help="Url to image", default=None)
    parser.add_argument("-f", help="Path to image", default=None)
    parser.add_argument(
        "--tags", help="Tags divided by space", default=[], nargs='+')
    parser.add_argument("--dry_run", help="Run script without saving output file",
                        action='store_true', default=False)
    return parser


def main() -> None:
    parser = get_cli_parser()
    args = parser.parse_args()
    print("pyIngnim v" + VERSION)

    cover = get_cover(args.u, args.f)
    if not cover:
        print("Url(-u) or input file(-f) must be specified.")
        sys.exit(1)

    if args.o or args.dry_run:
        bg = get_bg(cover)
        if args.tags:
            put_tags(bg, args.tags)
        canvas = ImageDraw.Draw(bg)
        if args.t:
            put_title(canvas, args.t)
        if args.d:
            put_desc(canvas, args.d)
        if args.r:
            put_mark(bg, canvas, args.r)
        if args.dry_run:
            bg.show()
            sys.exit(0)
        if args.o:
            bg.save(args.o)
        sys.exit(0)

    print("Output path(-o) or dry run(--dry_run) must be specified.")
    sys.exit(1)


if __name__ == '__main__':
    main()
