"""Generate app_icon.ico for Friedrich - Document Reader.

Concept: the obverse (portrait) side of the Augustale of Frederick II,
cropped from errors/625.jpg and masked to a circle on a transparent
background. Frederick II is "Friedrich" in German — hence the app name.

Run from the project root:
    python scripts/generate_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "errors" / "625.jpg"
OUTPUT_PATH = ROOT / "app_icon.ico"
PREVIEW_PATH = Path(__file__).resolve().parent / "preview_icon_256.png"

ICO_SIZES = [16, 32, 48, 64, 128, 256]

# Tight square crop around Frederick II's face (laurel + head + neck),
# excluding the bust and the CESAR AVG / IMPER inscriptions on the rim.
# Calibrated for the 1573x750 source image.
CROP_BOX = (200, 40, 600, 440)


def build_master(size: int = 1024) -> Image.Image:
    if not SOURCE_PATH.exists():
        raise SystemExit(f"Source image not found: {SOURCE_PATH}")
    src = Image.open(SOURCE_PATH).convert("RGBA")
    coin = src.crop(CROP_BOX).resize((size, size), Image.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(coin, (0, 0), mask=mask)
    return out


def main() -> None:
    master = build_master(1024)
    master.save(
        OUTPUT_PATH,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
    )
    master.save(PREVIEW_PATH)
    print(f"Icon written to {OUTPUT_PATH}")
    print(f"Preview written to {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
