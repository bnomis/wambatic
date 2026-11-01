#!/usr/bin/env python3
"""Build the rippling logo of the user guide's home page from the still mark.

Reads docs/assets/wambatic-mark.svg (a white box holding rows of squares in the heatmap's blue
ramp) and writes docs/assets/wambatic-mark-animated.svg: the same drawing with each square cycling
through three neighbouring steps of the ramp, starting a little later in each column, so the colour
ripples left to right. The left columns cycle the pale steps and the right columns the dark ones, so
the strip still darkens to the right; a random share of squares takes another range, so the ripple
reads as activity rather than a sweep. The animation is CSS keyframes inside the SVG, so it runs
when the file is shown as an <img>, and stops under prefers-reduced-motion, leaving the still mark.

The random choices come from a fixed seed, so the output is the same on every run. Run it by hand
after changing the still mark or the timing below (bin/animate-logo.sh); `--check` exits 1 when the
committed file is stale, without writing.

Every failure is one line on stderr and exit status 1.
"""

import argparse
import pathlib
import random
import sys
import xml.etree.ElementTree

import wambatic.reports.figures

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/assets/wambatic-mark.svg'
TARGET = ROOT / 'docs/assets/wambatic-mark-animated.svg'
SVG_NS = 'http://www.w3.org/2000/svg'

RAMP = wambatic.reports.figures.PALETTE['light'].sequential  # the heatmap's ramp, palest first
# Each band is the three ramp steps a square cycles through: from its first to its last and back.
BANDS = {'faint': RAMP[0:3], 'medium': RAMP[1:4], 'strong': RAMP[2:5]}
CYCLE_SECONDS = 3.2
COLUMN_DELAY_SECONDS = 0.22
JITTER_SECONDS = 0.5
OFF_BAND_SHARE = 0.25
SEED = 7


class LogoError(Exception):
    """The still mark cannot be read or holds no squares."""


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='animate-logo',
        description='Build the rippling home-page logo from the still mark.',
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='exit 1 if the animated logo is out of date, without writing it',
    )
    return parser.parse_args(argv)


def style_sheet() -> str:
    """The keyframes for each band, the shared animation, and the reduced-motion opt-out."""
    frames = ''.join(
        f'@keyframes {name}{{0%,100%{{fill:{first}}}50%{{fill:{last}}}75%{{fill:{middle}}}}}'
        for name, (first, middle, last) in BANDS.items()
    )
    return (
        frames
        + f'rect.q{{animation:{CYCLE_SECONDS:g}s ease-in-out infinite both}}'
        + '@media (prefers-reduced-motion:reduce){rect.q{animation:none}}'
    )


def column_band(column: int, columns: int) -> str:
    """The band for a column: the left third pale, the middle third middle, the right third dark."""
    return tuple(BANDS)[min(2, column * 3 // columns)]


def animate(still: str) -> str:
    """Return the animated SVG for the still mark's text.

    Raises:
        LogoError: the text is not valid SVG, or holds no squares besides the box.
    """
    xml.etree.ElementTree.register_namespace('', SVG_NS)
    try:
        root = xml.etree.ElementTree.fromstring(still)
    except xml.etree.ElementTree.ParseError as error:
        # auditme: accept[except-interpolation] the parser's message names the line and column
        raise LogoError(f'the still mark is not valid SVG: {error}') from error
    rects = root.findall(f'{{{SVG_NS}}}rect')
    squares = [rect for rect in rects if rect.get('rx') != '40']  # rx 40 is the box
    if not squares:
        raise LogoError('the still mark holds no squares')
    columns = sorted({float(rect.get('x', '0')) for rect in squares})
    chooser = random.Random(SEED)
    for rect in squares:
        column = columns.index(float(rect.get('x', '0')))
        band = column_band(column, len(columns))
        if chooser.random() < OFF_BAND_SHARE:
            band = chooser.choice(tuple(BANDS))
        # A negative delay starts the square part-way through its cycle, so it moves from load.
        start = column * COLUMN_DELAY_SECONDS + chooser.uniform(0, JITTER_SECONDS)
        rect.set('class', 'q')
        rect.set('style', f'animation-name:{band};animation-delay:{start - CYCLE_SECONDS:.2f}s')
    style = xml.etree.ElementTree.Element(f'{{{SVG_NS}}}style')
    style.text = style_sheet()
    root.insert(0, style)
    return xml.etree.ElementTree.tostring(root, encoding='unicode') + '\n'


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        animated = animate(SOURCE.read_text(encoding='utf-8'))
        current = TARGET.read_text(encoding='utf-8') if TARGET.exists() else None
        if args.check:
            if animated != current:
                sys.stderr.write(f'animate-logo: {TARGET.name} is stale; run bin/animate-logo.sh\n')
                return 1
            return 0
        if animated != current:
            TARGET.write_text(animated, encoding='utf-8')
    except (OSError, LogoError) as error:
        # auditme: accept[except-interpolation] the one line is the failure's own message
        sys.stderr.write(f'animate-logo: {error}\n')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
