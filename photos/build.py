#!/usr/bin/env python3
"""
Builds the gallery into _site/.

  photos/      <- drop your images here (jpg, png, webp, tif)
  index.html   <- the page template
  _site/       <- generated: what GitHub Pages serves

For every photo it makes a small grid version and a large viewing version
(WebP, colour profile kept, all other metadata such as GPS stripped), then
writes the list into the page. Newest capture date first.

Run locally:  python3 build.py && python3 -m http.server -d _site
"""
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "photos"
CACHE = ROOT / ".cache" / "img"   # survives between builds (also cached in CI)
OUT = ROOT / "_site"

THUMB_H = 720       # grid image height in px
FULL_EDGE = 2560    # viewer image long edge in px
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "photo"


def file_hash(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:10]


def capture_date(im: Image.Image):
    try:
        exif = im.getexif()
        raw = exif.get_ifd(0x8769).get(36867) or exif.get(306)   # DateTimeOriginal / DateTime
        if raw:
            return datetime.strptime(str(raw).strip("\x00 ")[:19], "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def to_rgb(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (0, 0, 0))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB") if im.mode != "RGB" else im


def save_webp(im: Image.Image, dest: Path, quality: int, icc):
    tmp = dest.with_suffix(".tmp")
    kw = {"quality": quality, "method": 5}
    if icc:
        kw["icc_profile"] = icc
    im.save(tmp, "WEBP", **kw)
    tmp.replace(dest)


def process(path: Path, used_slugs: set):
    digest = file_hash(path)
    slug = slugify(path.stem)
    base, n = slug, 2
    while slug in used_slugs:
        slug, n = f"{base}-{n}", n + 1
    used_slugs.add(slug)

    thumb = CACHE / f"{slug}-{digest}-t.webp"
    full = CACHE / f"{slug}-{digest}-f.webp"
    meta = CACHE / f"{slug}-{digest}.json"

    if thumb.exists() and full.exists() and meta.exists():
        info = json.loads(meta.read_text())
    else:
        with Image.open(path) as src:
            date = capture_date(src)
            icc = src.info.get("icc_profile")
            im = to_rgb(ImageOps.exif_transpose(src))

        big = im.copy()
        big.thumbnail((FULL_EDGE, FULL_EDGE), Image.Resampling.LANCZOS)
        save_webp(big, full, 84, icc)

        tw = max(1, round(im.width * THUMB_H / im.height))
        small = im.resize((tw, THUMB_H), Image.Resampling.LANCZOS) if im.height > THUMB_H else im.copy()
        save_webp(small, thumb, 80, icc)

        r, g, b = small.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
        info = {
            "w": big.width,
            "h": big.height,
            "c": f"#{r:02x}{g:02x}{b:02x}",
            "date": date.isoformat() if date else None,
        }
        meta.write_text(json.dumps(info))
        print(f"  + {path.name}")

    return {
        "id": slug,
        "w": info["w"],
        "h": info["h"],
        "c": info["c"],
        "t": f"img/{thumb.name}",
        "f": f"img/{full.name}",
        "_date": info["date"],
        "_name": path.name.lower(),
        "_files": [thumb, full, meta],
    }


def main():
    SRC.mkdir(exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    sources = sorted(p for p in SRC.rglob("*") if p.is_file() and p.suffix.lower() in EXTS)
    print(f"{len(sources)} photo(s) in {SRC.name}/")

    used, photos = set(), []
    for p in sources:
        try:
            photos.append(process(p, used))
        except Exception as e:  # one bad file shouldn't sink the whole gallery
            print(f"  ! skipped {p.name}: {e}", file=sys.stderr)

    # newest first; undated photos after dated ones, by filename
    dated = sorted((p for p in photos if p["_date"]), key=lambda p: p["_date"], reverse=True)
    undated = sorted((p for p in photos if not p["_date"]), key=lambda p: p["_name"])
    photos = dated + undated

    # drop cached files for photos that were removed or replaced
    keep = {f for p in photos for f in p["_files"]}
    for f in CACHE.iterdir():
        if f not in keep:
            f.unlink()

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "img").mkdir(parents=True)
    for p in photos:
        for f in p["_files"][:2]:
            shutil.copy2(f, OUT / "img" / f.name)

    public = [{k: v for k, v in p.items() if not k.startswith("_")} for p in photos]
    data = json.dumps(public, separators=(",", ":")).replace("</", "<\\/")
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    page, hits = re.subn(
        r'(<script id="photos" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + data + m.group(2),
        page,
        count=1,
        flags=re.S,
    )
    if not hits:
        sys.exit("index.html is missing the photos placeholder")
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print(f"built {len(public)} photo(s) -> {OUT.name}/")


if __name__ == "__main__":
    main()
