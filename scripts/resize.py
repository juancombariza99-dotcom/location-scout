#!/usr/bin/env python3
"""Make upright, EXIF-free JPEG copies of images (iPhone photos are often stored sideways).

    # Higgsfield references: photos/ -> refs/, 2048 px long edge (default)
    python3 scripts/resize.py places/<slug>/photos places/<slug>/refs

    # Smaller copies, e.g. for sharing
    python3 scripts/resize.py places/<slug>/previews out/previews --long-edge 1080

Subfolders are kept. GPS and other EXIF data are dropped.
Needs Python 3 + Pillow (pip install Pillow).
"""
import argparse, sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is missing. Install it with: pip install Pillow")

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--long-edge", type=int, default=2048)
    ap.add_argument("--quality", type=int, default=85)
    a = ap.parse_args()
    files = sorted(f for f in a.src.rglob("*") if f.suffix.lower() in EXTS and not f.name.startswith("."))
    if not files:
        sys.exit(f"No images in {a.src}")
    for f in files:
        try:
            im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        except Exception as err:  # e.g. HEIC without a plugin
            print(f"skip {f.name}: {err}")
            continue
        scale = a.long_edge / max(im.size)
        if scale < 1:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        out = (a.dst / f.relative_to(a.src)).with_suffix(".jpg")
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, "JPEG", quality=a.quality, optimize=True, progressive=True)
        print(f"{out}  {im.width}×{im.height}")


if __name__ == "__main__":
    main()
