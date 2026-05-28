#!/usr/bin/env python3
"""
Archive videos from a single Instagram account into an Obsidian vault.

Wraps gallery-dl (for the download) and build_notes (for Obsidian .md companions).
Uses your browser's existing Instagram session cookies — no password needed in the
script.

Output structure (inside --out):
    <date>_<shortcode>_<n>.mp4      videos (kept by gallery-dl)
    <date>_<shortcode>_<n>.mp4.json metadata sidecar (gallery-dl)
    captions/<date>_<shortcode>.md  Obsidian note with caption + embed link

Re-runs are safe: gallery-dl's --download-archive skips posts already fetched, so
you can stop and resume any time without re-downloading.

Usage:
    python instagram_archive.py \\
        --profile some_account \\
        --before 2025-03-16 \\
        --out ~/Documents/MyVault/videos \\
        --browser chrome
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from build_notes import build_notes


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--profile", required=True, help="Instagram handle (without @).")
    p.add_argument("--before", required=True,
                   help="Cutoff date YYYY-MM-DD. Only posts on or before this date are kept.")
    p.add_argument("--out", required=True,
                   help="Output folder. For Obsidian, put it inside your vault.")
    p.add_argument("--browser", default="firefox",
                   help="Browser to read cookies from: firefox/chrome/chromium/edge/brave (default: firefox).")
    p.add_argument("--cookies-file", help="Path to an exported cookies.txt (overrides --browser).")
    p.add_argument("--archive-file", default="./archive.txt",
                   help="gallery-dl download archive — tracks downloaded posts so reruns skip them.")
    p.add_argument("--notes-only", action="store_true",
                   help="Skip the download; only (re)generate Obsidian notes from existing JSON sidecars.")
    return p.parse_args()


def build_gallery_dl_cmd(args, cutoff: datetime) -> list:
    cmd = ["gallery-dl"]
    if args.cookies_file:
        cmd += ["--cookies", args.cookies_file]
    else:
        cmd += ["--cookies-from-browser", args.browser]

    filter_expr = (
        f"date <= datetime({cutoff.year}, {cutoff.month}, {cutoff.day}, 23, 59, 59) "
        f"and extension in ('mp4', 'mov')"
    )
    cmd += [
        "--dest", str(Path(args.out).expanduser()),
        "-o", "extractor.directory=[]",
        "--filter", filter_expr,
        "--filename", "{date:%Y-%m-%d}_{shortcode}_{num}.{extension}",
        "--write-metadata",
        "--download-archive", str(Path(args.archive_file).expanduser()),
        f"https://www.instagram.com/{args.profile}/",
    ]
    return cmd


def main():
    args = parse_args()
    cutoff = datetime.strptime(args.before, "%Y-%m-%d")
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.notes_only:
        if not shutil.which("gallery-dl"):
            print("ERROR: gallery-dl not installed. Run: pip install gallery-dl", file=sys.stderr)
            sys.exit(1)

        cmd = build_gallery_dl_cmd(args, cutoff)
        print("Running gallery-dl (output streams below)…\n")
        # Stream gallery-dl's output to terminal directly — no Python-side buffering.
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            print(f"\ngallery-dl exited with code {rc}", file=sys.stderr)
            sys.exit(rc)

    print("\nBuilding Obsidian notes…")
    n = build_notes(out_dir, args.profile)
    print(f"Created {n} note(s) in {out_dir / 'captions'}.")


if __name__ == "__main__":
    main()
