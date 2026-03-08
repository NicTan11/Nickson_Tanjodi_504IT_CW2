import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw


def gen_image(width, height, seed):
    rnd = random.Random(seed)

    # random background colour
    img = Image.new("RGB", (width, height),
                    (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
    draw = ImageDraw.Draw(img)

    # draw rectangles
    for _ in range(60):
        x1 = rnd.randrange(width)
        y1 = rnd.randrange(height)
        x2 = rnd.randrange(width)
        y2 = rnd.randrange(height)

        x0, x1 = sorted((x1, x2))
        y0, y1 = sorted((y1, y2))

        draw.rectangle([x0, y0, x1, y1],
                       outline=(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)),
                       width=2)

    # draw lines
    for _ in range(40):
        x1 = rnd.randrange(width)
        y1 = rnd.randrange(height)
        x2 = rnd.randrange(width)
        y2 = rnd.randrange(height)

        draw.line([x1, y1, x2, y2],
                  fill=(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)),
                  width=2)

    draw.text((10, 10), f"{width}x{height} seed={seed}", fill=(255, 255, 255))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--sizes", nargs="+", default=["640x480"])
    ap.add_argument("--format", choices=["jpg", "png"], default="jpg")
    ap.add_argument("--seed", type=int, default=123)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # parse sizes like ["640x480", "800x600"]
    sizes = []
    for s in args.sizes:
        w, h = s.lower().split("x")
        sizes.append((int(w), int(h)))

    for i in range(args.count):
        w, h = sizes[i % len(sizes)]
        img = gen_image(w, h, args.seed + i)

        filename = f"img_{i:05d}.{args.format}"
        path = out_dir / filename

        if args.format == "jpg":
            img.save(path, quality=90, optimize=True)
        else:
            img.save(path)

    print(f"Generated {args.count} images into: {out_dir.resolve()}")


if __name__ == "__main__":
    main()