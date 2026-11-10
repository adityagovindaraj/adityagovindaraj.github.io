# Gallery

A wordless photo gallery. Black background, photos in justified rows at their true shape, tap one to view it full-screen.

## Set up (once)

1. Create a GitHub repository and push these files to its `main` branch.
   - Name it `<your-username>.github.io` to serve at `https://<your-username>.github.io/`
   - Any other name serves at `https://<your-username>.github.io/<repo-name>/`
2. In the repo, go to **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**.

## Add photos

Drop images (JPG, PNG, WebP, TIFF) into `photos/` and push. The site rebuilds itself in a minute or two.
Remove a file to remove it from the gallery. Subfolders are fine.

- **Order:** newest capture date first (from the camera's EXIF data); photos with no date go last, by filename.
- **Sizes:** each photo gets a 720px-tall grid version and a 2560px viewing version, in WebP with the colour profile kept.
- **Privacy:** the published images have all metadata stripped (including GPS). The originals in `photos/` are not stripped, and on a free GitHub plan the repository must be public for Pages to work, so anyone can download them. Export without location data if that matters.
- **Repo size:** GitHub rejects files over 100 MB and prefers repositories under about 1 GB. Exporting at around 3000–4000px on the long edge (JPEG quality ~90) keeps each file to a couple of MB with no visible loss on the site.

## How it browses

| | Phone / tablet | Computer |
|---|---|---|
| Open a photo | Tap | Click |
| Next / previous | Swipe sideways, or tap the right / left edge | Arrow keys, trackpad swipe, or click the right / left third |
| Back to the grid | Swipe down, tap the middle, or the back button | Esc, click the middle, or the back button |

Every photo has its own link (`…/#img-1234`), so you can share a single image.

## Preview locally

```
pip install pillow
python3 build.py
python3 -m http.server -d _site
```

Then open http://localhost:8000.

## Tweaks

- Browser tab title: the `<title>` line in `index.html`.
- Gap between photos: `--gap` and `GAP` in `index.html` (keep both the same).
- Row height: `targetHeight()` in `index.html`.
