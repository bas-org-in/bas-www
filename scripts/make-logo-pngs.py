"""Make the web copies of the BAS logo from the two master JPEG files (ST-86).

Usage:
  uv run --no-project --with pillow==12.3.0 python -I scripts/make-logo-pngs.py

The masters are public/files/bas_logo.jpg (black on white) and
public/files/bas_logo_white.jpg (white on black), 6000 x 4052 px. The script
writes public/files/bas_logo_black.png and public/files/bas_logo_white.png,
480 x 324 px, with a transparent background. 480 px is three times the widest
size that the site shows, 160 px.
"""

from pathlib import Path

from PIL import Image

FILES = Path(__file__).resolve().parent.parent / "public" / "files"
SIZE = (480, 324)
# JPEG noise near pure black and pure white must not show as a faint box.
LOW, HIGH = 8, 247


def ink(level):
    """How much of the logo a pixel holds, 0 to 255, from its distance to the background."""
    return round(255 * min(max(level - LOW, 0), HIGH - LOW) / (HIGH - LOW))


def make(master, background_is_white, grey, target):
    levels = [ink(255 - v if background_is_white else v) for v in range(256)]
    alpha = Image.open(FILES / master).convert("L").point(levels).resize(SIZE, Image.Resampling.LANCZOS)
    logo = Image.merge("LA", (Image.new("L", SIZE, grey), alpha))
    logo.save(FILES / target, optimize=True)
    print(target, (FILES / target).stat().st_size, "bytes")


make("bas_logo.jpg", True, 0, "bas_logo_black.png")
make("bas_logo_white.jpg", False, 255, "bas_logo_white.png")
