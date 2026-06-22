#!/usr/bin/env python3
"""Generate or patch title-screen creator/version tiles."""

from __future__ import annotations

import argparse
from pathlib import Path


WHITE = 0
LIGHT = 1
DARK = 3

TILE_SIZE = 16
STRIP_TILE_COUNT = 15
STRIP_TILE_START = None
TEXT_X = 0
TEXT_Y = 1
COPY_Y = 0

GLYPHS = {
    "copy": [
        ".+***+.",
        ".*...*+",
        "*.+**.*",
        "*.*...*",
        "*.+**.*",
        "+*...*+",
        ".+***+.",
    ],
    "D": ["****.", "**.**", "**.**", "**.**", "****."],
    "P": ["*****", "**..*", "*****", "**...", "**..."],
    "S": ["*****", "**...", "*****", "...**", "*****"],
    "V": ["**.**", "**.**", "**+**", ".***.", "..*.."],
    "0": ["+***+", "**.**", "**.**", "**.**", "+***+"],
    "1": ["***", ".**", ".**", ".**", ".**"],
    "2": ["***+", "..**", "+***", "**..", "****"],
    "3": ["****", "..**", "****", "..**", "****"],
    "4": ["**.**", "**.**", "*****", "...**", "...**"],
    "5": ["*****", "**...", "****.", "...**", "****."],
    "6": ["+****", "**...", "****.", "**.**", "+***+"],
    "7": ["*****", "...**", "..**.", ".**..", ".**.."],
    "8": ["+***+", "**.**", "+***+", "**.**", "+***+"],
    "9": ["+***+", "**.**", "+****", "...**", "****+"],
    ".": ["..", "..", "..", "**", "**"],
    "-": ["....", "....", "****", "....", "...."],
    " ": ["..", "..", "..", "..", ".."],
}


def pixel(ch: str) -> int:
    if ch == "*":
        return DARK
    if ch == "+":
        return LIGHT
    return WHITE


def encode_2bpp(canvas: list[list[int]]) -> bytes:
    width = len(canvas[0])
    out = bytearray()
    for tile_x in range(0, width, 8):
        for y in range(8):
            lo = 0
            hi = 0
            for x in range(8):
                color = canvas[y][tile_x + x]
                bit = 7 - x
                lo |= (color & 1) << bit
                hi |= ((color >> 1) & 1) << bit
            out.extend((lo, hi))
    return bytes(out)


def render(
    year: str,
    version: str,
    prefix: str,
    tiles: int,
    text_x: int,
    include_copy: bool,
) -> bytes:
    text = f"{year} {prefix} {version}".upper()
    width = tiles * 8
    canvas = [[WHITE for _ in range(width)] for _ in range(8)]
    x = text_x

    if include_copy:
        x = draw_glyph(canvas, x, COPY_Y, GLYPHS["copy"])
    for ch in text:
        if ch not in GLYPHS:
            raise SystemExit(f"Unsupported title version character: {ch!r}")
        glyph = GLYPHS[ch]
        glyph_width = len(glyph[0])
        if x + glyph_width > width:
            raise SystemExit(f"Title version text is too wide for {tiles} tiles: {text!r}")
        x = draw_glyph(canvas, x, TEXT_Y, glyph)

    return encode_2bpp(canvas)


def draw_glyph(canvas: list[list[int]], x: int, y: int, glyph: list[str]) -> int:
    width = len(glyph[0])
    for gy, row in enumerate(glyph):
        for gx, value in enumerate(row):
            if value != ".":
                canvas[y + gy][x + gx] = pixel(value)
    return x + width + 1


def main() -> None:
    global DARK

    parser = argparse.ArgumentParser()
    parser.add_argument("--year", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prefix", default="SPP")
    parser.add_argument("--tiles", default=STRIP_TILE_COUNT, type=int)
    parser.add_argument("--tile-start", type=lambda value: int(value, 0))
    parser.add_argument("--text-x", default=TEXT_X, type=int)
    parser.add_argument("--dark", default=DARK, choices=(2, 3), type=int)
    parser.add_argument("--include-copy", action="store_true")
    args = parser.parse_args()

    DARK = args.dark
    strip = render(
        args.year,
        args.version,
        args.prefix,
        args.tiles,
        args.text_x,
        args.include_copy,
    )

    if args.tile_start is None:
        data = strip
    else:
        data = bytearray(args.output.read_bytes())
        start = args.tile_start * TILE_SIZE
        end = start + args.tiles * TILE_SIZE
        data[start:end] = strip
        data = bytes(data)

    if args.output.exists() and args.output.read_bytes() == data:
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)


if __name__ == "__main__":
    main()
