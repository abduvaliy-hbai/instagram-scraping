# instagram-archive

Download videos from a single Instagram account and turn each post into an [Obsidian](https://obsidian.md) note with caption, hashtags, and an embedded playable video.

Built for one specific use case: **archiving content from an account you own or have permission to download from, before it disappears** (account sold, deleted, deactivated). It is not designed for mass scraping.

## What it does

For every video post on or before a cutoff date:

1. Downloads the video as `<YYYY-MM-DD>_<shortcode>_<n>.mp4` (carousels with multiple videos get `_1`, `_2`, …)
2. Writes a gallery-dl JSON metadata sidecar alongside each video
3. Creates an Obsidian markdown note at `captions/<YYYY-MM-DD>_<shortcode>.md` containing:
   - YAML frontmatter (date, original Instagram URL, source handle, hashtags)
   - An Obsidian embed `![[…mp4]]` that plays the video inline
   - The full original caption

Re-runs are safe — a gallery-dl download archive (`archive.txt`) tracks fetched posts, so you can stop and resume any time.

## Requirements

- Python 3.10+
- A browser logged into Instagram (Chrome or Firefox are easiest)
- The Instagram account you're archiving must be visible to your logged-in account (follow it if it's private)

## Install

```bash
git clone https://github.com/abduvaliy-hbai/instagram-scraping.git
cd instagram-scraping

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you plan to use Chrome cookies on Linux, you also need GNOME keyring support — `secretstorage` (already in `requirements.txt`) handles this. On Ubuntu, you may additionally need `python3-dev` and `libssl-dev` for the build.

## Usage

```bash
python instagram_archive.py \
    --profile some_account \
    --before 2025-03-16 \
    --out ~/Documents/MyVault/videos \
    --browser firefox
```

### Arguments

| Flag | Required | Default | Description |
|---|---|---|---|
| `--profile` | yes | — | Instagram handle (no `@`) |
| `--before` | yes | — | Cutoff date `YYYY-MM-DD`, inclusive — posts on or before this date are kept |
| `--out` | yes | — | Output directory; place it inside your Obsidian vault for embeds to resolve |
| `--browser` | no | `firefox` | Browser to read cookies from: `firefox` / `chrome` / `chromium` / `edge` / `brave` |
| `--cookies-file` | no | — | Path to an exported `cookies.txt` (overrides `--browser`) |
| `--archive-file` | no | `./archive.txt` | gallery-dl download archive (rerun-safe state) |
| `--notes-only` | no | off | Skip the download; only (re)generate Obsidian notes from existing JSON sidecars |

### Browser cookies

The script uses your **existing browser session** to authenticate — it does not ask for your Instagram password.

- **Firefox:** keep it open while the script runs. No setup needed.
- **Chrome:** must be **completely closed** before running (Chrome locks its cookie database while running). After cookies are loaded into memory (you'll see `[cookies][info] Extracted N cookies`), you can reopen Chrome.

### Output layout

For an output directory of `~/Documents/MyVault/videos`:

```
videos/
├── 2024-08-12_C9abcDEFGHI_1.mp4
├── 2024-08-12_C9abcDEFGHI_1.mp4.json
├── 2024-08-13_C9xyzZZZZZZ_1.mp4
├── 2024-08-13_C9xyzZZZZZZ_1.mp4.json
└── captions/
    ├── 2024-08-12_C9abcDEFGHI.md
    └── 2024-08-13_C9xyzZZZZZZ.md
```

In Obsidian, open any `.md` file and the video plays inline via the `![[…mp4]]` embed. The `.json` files are optional — they're gallery-dl's metadata. You can delete them once notes are generated, or keep them for reruns.

### Manual note (re)generation

If you ever want to rebuild the notes from the JSON sidecars without touching the downloads:

```bash
python build_notes.py /path/to/videos some_account
```

or

```bash
python instagram_archive.py --notes-only --profile some_account --before 2025-03-16 --out /path/to/videos
```

## How it works

Under the hood:

1. **gallery-dl** walks the profile newest-first, applying a date filter (`date <= cutoff`) and a media-type filter (`extension in ('mp4', 'mov')`). It writes each match plus a `.json` metadata sidecar.
2. **build_notes.py** walks the JSON sidecars, groups them by post shortcode (so multi-video carousels become one note), and writes the Obsidian markdown.

The download itself can take a while: gallery-dl deliberately paces requests (~7–8 seconds between profile pages) to stay under Instagram's rate limits. For an account with 1,500 posts, expect 5+ minutes just to walk the index.

## Things to know

- **Filter is applied during pagination**, but Instagram returns posts newest-first. To find posts before the cutoff, gallery-dl still has to walk every newer post first. There is no way to skip ahead by date — that's an Instagram limitation.
- **Resume is automatic**: if interrupted, just rerun the same command. `archive.txt` records every successfully downloaded post; reruns skip them.
- **Multiple browser profiles**: if your Instagram session is in a non-default browser profile, gallery-dl's auto-detect may miss it. Easier path is to export cookies to a file (extensions like "Get cookies.txt LOCALLY") and use `--cookies-file`.

## Tools that didn't work (notes for future me)

We tried two other libraries before settling on gallery-dl:

- **instaloader** — Instagram's API changes broke profile lookups. `ProfileNotExistsException` even for public, followed accounts.
- **yt-dlp** — its Instagram profile extractor returns "Unable to extract data". Individual posts may still work, but not whole-profile walks.

gallery-dl was the only one of the three that reliably handled both profile walking and Instagram's anti-scraping at time of writing (late 2025 / early 2026). This is a moving target.

## License

Choose one (e.g. MIT) and add a `LICENSE` file.

## Ethics

Only use this for accounts you own, accounts that have given you explicit permission, or research/archival with appropriate consent. Public visibility is not the same as a license to redistribute.
