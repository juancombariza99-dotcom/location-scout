#!/usr/bin/env python3
"""Build the scout page and the shots grid for one place.

    python3 scripts/build.py places/<slug>
    python3 scripts/build.py places/<slug> --out /some/other/folder

Reads   <place>/place.json, <place>/plan.svg and the images it points to.
Writes  <place>/scout.html and <place>/shots.html (single files, images embedded).

Needs Python 3 + Pillow (pip install Pillow).
"""
import argparse, base64, html, io, json, re, sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is missing. Install it with: pip install Pillow")

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

SPOT_W = 640      # spot photos on the scout page (3:4)
PREVIEW_W = 480   # previews on both pages (9:16)
QUALITY = 75
GRID_MAX = 18
PER_PAGE = 6
LEGEND_COLORS = {"cam", "cam-soft", "light", "glass", "brick", "brick-soft", "shade", "accent", "accent-soft"}
NUMBER_WORDS = "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve".split()

_cache = {}


def data_uri(place: Path, rel: str, width: int) -> str:
    """Upright, EXIF-free, resized JPEG as a data URI."""
    key = (rel, width)
    if key not in _cache:
        path = place / rel
        if not path.is_file():
            sys.exit(f"Missing image: {path}")
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        _cache[key] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return _cache[key]


def js(value, **kw) -> str:
    """JSON that is safe inside a <script> tag."""
    return json.dumps(value, **kw).replace("</", "<\\/")


def rich(text: str) -> str:
    """Escape, then turn **bold** into <b>bold</b>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(text, quote=False))


def fill(template: str, values: dict) -> str:
    """Replace every __KEY__ in one pass, so inserted text is never re-scanned."""
    def sub(m):
        if m.group(1) not in values:
            sys.exit(f"Template placeholder __{m.group(1)}__ has no value")
        return values[m.group(1)]
    return re.sub(r"__([A-Z_]+)__", sub, template)


def check(p: dict, place: Path):
    errors = []
    for k in ("slug", "name", "spots", "buckets", "shots", "grid"):
        if k not in p:
            errors.append(f"place.json needs '{k}'")
    if errors:
        sys.exit("\n".join(errors))
    if not re.fullmatch(r"[a-z0-9-]+", p["slug"]):
        errors.append("slug: lowercase letters, numbers and dashes only")
    ids = [s["id"] for s in p["spots"]]
    if len(ids) != len(set(ids)):
        errors.append("spots: duplicate id")
    for s in p["shots"]:
        if s.get("spot") not in ids:
            errors.append(f"shot '{s.get('title')}': spot '{s.get('spot')}' is not in spots")
        if s.get("bucket") not in p["buckets"]:
            errors.append(f"shot '{s.get('title')}': bucket '{s.get('bucket')}' is not in buckets")
    if len(p["grid"]) > GRID_MAX:
        errors.append(f"grid: {len(p['grid'])} shots, max is {GRID_MAX}")
    for c in p.get("legend", []):
        if c["color"] not in LEGEND_COLORS:
            errors.append(f"legend: unknown color '{c['color']}' (use one of {sorted(LEGEND_COLORS)})")
    if not (place / "plan.svg").is_file():
        errors.append(f"Missing {place / 'plan.svg'}")
    if errors:
        sys.exit("place.json problems:\n- " + "\n- ".join(errors))


def build_scout(p: dict, place: Path) -> str:
    routine = p.get("routine", {})
    steps = routine.get("steps", [])
    img = {s["photo"]: data_uri(place, s["photo"], SPOT_W) for s in p["spots"]}
    pv = {x["preview"]: data_uri(place, x["preview"], PREVIEW_W)
          for x in steps + p["shots"] if x.get("preview")}

    plan = (place / "plan.svg").read_text(encoding="utf-8")
    plan = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", plan).strip()
    plan = re.sub(r"\s*<metadata>.*?</metadata>", "", plan, flags=re.S)  # file metadata, not needed inline
    plan = plan.replace(' xmlns:c2pa="http://c2pa.org/manifest"', "")

    legend = "".join(
        f'\n      <span><i class="sw" style="background:var(--{c["color"]})"></i>{html.escape(c["label"], quote=False)}</span>'
        for c in p.get("legend", []))
    legend = f'<div class="legend">{legend}\n    </div>'

    def items(block):
        return "\n".join(f"        <li>{rich(x)}</li>" for x in block.get("items", []))

    n = len(p["spots"])
    word = NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)
    n_photos = len([f for f in (place / "photos").iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".heic"}]) \
        if (place / "photos").is_dir() else 0
    e = lambda s: html.escape(s, quote=False)

    return fill((TEMPLATES / "scout-page.html").read_text(encoding="utf-8"), {
        "PAGE_TITLE": e(p.get("page_title", f"{p['name']} Scout")),
        "NAME": e(p["name"]),
        "MAP_INTRO": e(p.get("map_intro", f"Pieced together from your {n_photos} photos, so walls and sizes are estimates. "
                                         "What matters is where the camera stands and which way it looks.")),
        "PLAN": plan,
        "LEGEND": legend,
        "SPOTS_TITLE": e(p.get("spots_title", f"{word} spots")),
        "ROUTINE_TITLE": e(routine.get("title", "")),
        "ROUTINE_INTRO": e(routine.get("intro", "")),
        "RESET_TITLE": e(p.get("reset", {}).get("title", "5-minute reset before filming")),
        "RESET": items(p.get("reset", {})),
        "LIGHT_TITLE": e(p.get("light", {}).get("title", "Light in this place")),
        "LIGHT": items(p.get("light", {})),
        "FOOTER": e(p.get("footer", "Checkmarks are saved on this device only.")),
        "SLUG": p["slug"],
        "NOTES": js(p.get("notes", {}), ensure_ascii=False, indent=1),
        "IMG": js(img),
        "PV": js(pv),
        "SPOTS": js(p["spots"], ensure_ascii=False),
        "ROUTINE": js(steps, ensure_ascii=False),
        "BUCKETS": js(p["buckets"], ensure_ascii=False),
        "SHOTS": js(p["shots"], ensure_ascii=False),
    })


def build_grid(p: dict, place: Path) -> str:
    grid = p["grid"]
    pages = []
    for start in range(0, len(grid), PER_PAGE):
        figs = []
        for g in grid[start:start + PER_PAGE]:
            t, line = html.escape(g["title"]), g.get("line", "")
            figs.append(f'<figure><img src="{data_uri(place, g["preview"], PREVIEW_W)}" alt="{t}" loading="lazy">'
                        f'<figcaption><b>{t}</b>{f"<p>{html.escape(line)}</p>" if line else ""}</figcaption></figure>')
        pages.append(f'<section class="page" aria-label="Page {start // PER_PAGE + 1}">' + "".join(figs) + "</section>")
    count = f"{len(grid)} shot{'s' if len(grid) != 1 else ''}"
    sub = f"{p['grid_subtitle']} · {count}" if p.get("grid_subtitle") else count
    return fill((TEMPLATES / "shots-grid.html").read_text(encoding="utf-8"), {
        "TITLE": html.escape(p.get("grid_title", f"{p['name']} Shots"), quote=False),
        "SUB": html.escape(sub, quote=False),
        "NP": str(max(1, len(pages))),
        "PAGES": "".join(pages),
    })


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("place", type=Path, help="place folder with place.json")
    ap.add_argument("--out", type=Path, help="output folder (default: the place folder)")
    a = ap.parse_args()
    place = a.place.resolve()
    p = json.loads((place / "place.json").read_text(encoding="utf-8"))
    check(p, place)
    out = (a.out or place).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for name, page in (("scout.html", build_scout(p, place)), ("shots.html", build_grid(p, place))):
        (out / name).write_text(page, encoding="utf-8")
        print(f"{out / name}  ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
