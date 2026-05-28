#!/usr/bin/env python3
"""
Generate Obsidian .md companion notes from gallery-dl's JSON sidecars.

For each video file in the input dir, finds its matching .json sidecar
(written by gallery-dl --write-metadata), groups by post shortcode (so
multi-video carousels become one note), and writes <date>_<shortcode>.md
into a `captions/` subfolder.

Usage:
    python build_notes.py <videos_dir> <profile_name>
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def fmt_date(d) -> str:
    if not d:
        return "unknown"
    s = str(d)
    return s[:10] if len(s) >= 10 else s


def extract_hashtags(caption: str) -> list:
    tags, seen = [], set()
    for word in (caption or "").split():
        if not word.startswith("#") or len(word) <= 1:
            continue
        tag = word[1:].rstrip(".,!?;:)")
        if tag and all(c.isalnum() or c == "_" for c in tag) and tag.lower() not in seen:
            seen.add(tag.lower())
            tags.append(tag)
    return tags


def write_md(md_path: Path, meta: dict, video_filenames: list, profile: str):
    date_str = fmt_date(meta.get("date") or meta.get("post_date"))
    caption = (meta.get("description") or "").strip()
    shortcode = meta.get("shortcode") or meta.get("post_shortcode") or ""
    url = f"https://instagram.com/p/{shortcode}"
    tags = extract_hashtags(caption)

    fm = [
        "---",
        f"date: {date_str}",
        f"url: {url}",
        f"source: {profile}",
    ]
    if tags:
        fm.append("hashtags: [" + ", ".join(tags) + "]")
    fm.append("---")

    embeds = "\n".join(f"![[{f}]]" for f in video_filenames)
    md_path.write_text("\n".join(fm) + "\n\n" + embeds + "\n\n" + caption + "\n", encoding="utf-8")


def build_notes(out_dir: Path, profile: str) -> int:
    """Walk JSON sidecars, group by shortcode, write .md notes. Returns the count created."""
    out_dir = Path(out_dir).expanduser()
    notes_dir = out_dir / "captions"
    notes_dir.mkdir(exist_ok=True)

    grouped = defaultdict(list)
    for json_path in sorted(out_dir.glob("*.json")):
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {json_path.name}: {e}", file=sys.stderr)
            continue
        video = json_path.with_suffix("")  # strip .json → leaves <name>.mp4
        if not video.exists() or video.suffix.lower() not in (".mp4", ".mov"):
            continue
        shortcode = meta.get("shortcode") or meta.get("post_shortcode")
        if not shortcode:
            continue
        grouped[shortcode].append((video.name, meta))

    created = 0
    for shortcode, files in grouped.items():
        files.sort()
        _, meta = files[0]
        date_str = fmt_date(meta.get("date") or meta.get("post_date"))
        md_path = notes_dir / f"{date_str}_{shortcode}.md"
        write_md(md_path, meta, [f for f, _ in files], profile)
        created += 1
    return created


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    out_dir = Path(sys.argv[1])
    profile = sys.argv[2]
    if not out_dir.is_dir():
        print(f"ERROR: not a directory: {out_dir}", file=sys.stderr)
        sys.exit(1)
    n = build_notes(out_dir, profile)
    print(f"Created {n} Obsidian note(s) in {out_dir / 'captions'}")


if __name__ == "__main__":
    main()
