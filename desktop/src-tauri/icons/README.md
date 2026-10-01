# The DAH app icon — specification

`icon.png` is the source of truth; `icon.icns` (macOS) and `icon.ico` (Windows)
are generated from it. This file records the geometry the icon must hold, why
it holds it, and how to regenerate and verify it.

The icon has been fixed three times for being the wrong size, and each fix was
a measurement, not a guess. The numbers below are what stopped that loop.

## 1. The reference: Apple's own app icons

Apple does not ship a template image, but it ships the template's geometry in
every built-in app. Measured on `/System/Applications` icons
(Calculator, Notes, Mail, TextEdit — all identical):

| Property | Measured on Apple's icons | At 1024 canvas |
|---|---|---|
| Opaque tile span | 207 px of a 256 px canvas (**80.5%**) | **824 × 824** |
| Margin, each side | 25 px of 256 (~9.8%), symmetric | **100 px** |
| Corner (squircle) radius | ~56 px at 256 | ~224 px at 1024 |
| Tile shape | superellipse (squircle), not a plain rounded rect |

The single most important number here is **80.5%**: an Apple app icon does not
fill its canvas. The visible squircle is inset, leaving roughly a tenth of the
canvas as transparent margin on every side. The Dock and Finder scale the icon
*resource* to the tile they draw, so an icon whose tile spans 100% of its
canvas renders about 24% wider than every other app — which is exactly what
"the icon looks bigger than standard" means.

## 2. DAH's specification

Measured on `icon.png` (1024 × 1024, RGBA):

| Property | Value | Note |
|---|---|---|
| Canvas | 1024 × 1024 | the size Apple's grid and `iconutil` expect |
| Tile span | x and y **100–924** (824 px, **80.5%**) | matches Apple |
| Margins | 100 px left/right/top/bottom (symmetric) | matches Apple |
| Tile shape | squircle, corner radius **180 px at 824 scale** (≈224 px at 1024) | the v0.3.1 mask, rescaled |
| Tile colour | `rgb(18, 27, 44)` flat navy | the mask is the only alpha |
| Glyph | bar chart, 424 × 419 px (**51% of the tile**), centred 511, 510 | the v0.3.2 ratio, preserved |
| Glyph colours | `rgb(77, 208, 225)` cyan, `rgb(255, 196, 87)` amber, `rgb(148, 163, 184)` grey | the chart's marks |

Two properties are load-bearing and must survive any edit:

- **The tile spans 80.5% of the canvas, symmetric.** This is the one that made
  the icon oversized; getting it wrong is what every prior fix chased.
- **The glyph stays near 51% of the tile.** At 68% it read as oversized
  *inside* the tile (v0.3.2's finding). The glyph-to-tile ratio is independent
  of the tile-to-canvas ratio, so scaling the tile must not drag the glyph with
  it — and scaling the glyph must not touch the tile.

## 3. The history, so the question does not reopen

| Release | Change | Finding it answered |
|---|---|---|
| v0.3.0 | full-bleed 1024 square, 60 px corner radius | — (the original) |
| v0.3.1 | re-masked to the squircle, ~224 px radius | the square corners made it render as a tile, not a Ventura icon |
| v0.3.2 | glyph scaled 68% → 52% of the canvas | the glyph still read as oversized *inside* the tile |
| **v0.3.9** | **whole icon scaled to a 824 px tile (80.5%), centred** | **the tile was 100% of the canvas — ~24% wider than Apple's 80.5% template** |

v0.3.1 and v0.3.2 fixed the shape and the glyph but left the tile at full
canvas size, which is the property that actually sets an icon's footprint.
v0.3.9 scaled the tile and glyph *together* — a uniform 0.8047 scale — so the
glyph's ratio inside the tile is untouched and only the footprint changed.

## 4. Regenerating the icon set

`icon.png` is the source. From it, every standard size is downscaled with a
high-quality filter and packaged with `iconutil`. `iconutil` requires the
input directory to be named with an `.iconset` suffix — anything else fails
with `Invalid Iconset`.

```bash
cd desktop/src-tauri/icons

# 1. Regenerate every standard size from icon.png (LANCZOS).
python3 - <<'EOF'
from PIL import Image
src = Image.open('icon.png').convert('RGBA')
for s, at2 in {16: 32, 32: 64, 128: 256, 256: 512, 512: 1024}.items():
    src.resize((s, s), Image.LANCZOS).save(f'/tmp/dah.iconset/icon_{s}x{s}.png')
    src.resize((at2, at2), Image.LANCZOS).save(f'/tmp/dah.iconset/icon_{s}x{s}@2x.png')
EOF

# 2. Package the .icns (macOS) and .ico (Windows).
iconutil -c icns -o icon.icns /tmp/dah.iconset
python3 -c "from PIL import Image; Image.open('icon.png').save('icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
```

Then rebuild the bundle so the new icon lands in the app and the DMG:

```bash
cd server && ./build_sidecar.sh        # only if the version bumped
cd ../desktop && npm run build         # web bundle + tauri build (.app + DMG)
./bundle_dmg.sh <version> x86_64-apple-darwin   # the deterministic DMG
```

## 5. Verifying the geometry

The icon is an asset, but its geometry is a contract, so it is checked
numerically rather than by eye. Run this after any icon edit:

```bash
cd desktop/src-tauri/icons
python3 - <<'EOF'
from PIL import Image
im = Image.open('icon.png').convert('RGBA'); px = im.load(); w, h = im.size
xs = [x for y in range(h) for x in range(w) if px[x, y][3] > 128]
fill = (max(xs) - min(xs) + 1) / w
left, right = min(xs), w - 1 - max(xs)
assert (w, h) == (1024, 1024), 'canvas must be 1024'
assert abs(fill - 0.805) < 0.01, f'tile fill {fill:.3f}, expected 0.805'
assert abs(left - right) <= 1, f'margins {left}/{right} are not symmetric'
print(f'OK: tile {max(xs)-min(xs)+1}px, fill {fill:.1%}, margins {left}/{right}')
EOF
```

If a future edit changes the artwork, re-derive the glyph numbers in §2 the
same way: the glyph is every opaque pixel that differs from the tile's
background colour, and its ratio is taken against the 824 px tile, not the
canvas.

## 6. Apple's icon grid, for reference

- Canvas 1024 × 1024; the squircle occupies the inner 824 × 824.
- Corner radius ≈224 px at 1024 scale (a superellipse, not a plain rounded
  rect — the curve is fuller near the corners than `border-radius` draws).
- Artwork stays inside the tile; nothing crosses the squircle's edge.
- No text in the icon beyond the artwork itself; no dropped shadows or
  photographic backgrounds (Ventura icons are flat).
