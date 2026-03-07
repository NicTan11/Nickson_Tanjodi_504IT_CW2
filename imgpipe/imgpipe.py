import argparse
import csv
import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

from PIL import Image, ImageFilter

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_images(folder):
    """Find all image files recursively."""
    folder = Path(folder)
    files = []
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            files.append(p)
    files.sort()
    return files


def apply_ops(img, ops):
    """
    Supported ops:
      resize:WxH   e.g. resize:800x600
      gray
      blur:R       e.g. blur:1.2
      sharpen
    """
    for op in ops:
        if op.startswith("resize:"):
            size = op.split(":", 1)[1]
            w, h = size.lower().split("x")
            img = img.resize((int(w), int(h)))

        elif op == "gray":
            img = img.convert("L").convert("RGB")

        elif op.startswith("blur:"):
            r = float(op.split(":", 1)[1])
            img = img.filter(ImageFilter.GaussianBlur(radius=r))

        elif op == "sharpen":
            img = img.filter(ImageFilter.SHARPEN)

        else:
            raise ValueError("Unknown op: " + op)

    return img


def process_one(job):
    """
    Job is a tuple because ProcessPoolExecutor needs picklable input.
    Returns a dict row for results.csv.
    """
    src, in_root, out_root, ops, out_fmt, quality = job

    src = Path(src)
    in_root = Path(in_root)
    out_root = Path(out_root)

    rel = src.relative_to(in_root)
    dst = (out_root / rel).with_suffix("." + out_fmt.lower())
    dst.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "rel_path": str(rel),
        "pid": os.getpid(),          # proof: shows worker process ID
        "bytes_in": 0,
        "w_in": 0,
        "h_in": 0,
        "w_out": 0,
        "h_out": 0,
        "t_read_ms": 0.0,
        "t_proc_ms": 0.0,
        "t_write_ms": 0.0,
        "ok": 0,
        "err": ""
    }

    try:
        row["bytes_in"] = src.stat().st_size

        # READ (includes decode)
        t0 = time.perf_counter()
        img = Image.open(src)
        img.load()
        t1 = time.perf_counter()

        row["w_in"], row["h_in"] = img.size

        # PROCESS
        img2 = apply_ops(img, ops)
        row["w_out"], row["h_out"] = img2.size
        t2 = time.perf_counter()

        # WRITE (no kwargs, Pillow infers format from file extension)
        if out_fmt.lower() in ("jpg", "jpeg"):
            img2.save(dst, quality=quality, optimize=True)
        else:
            img2.save(dst)

        t3 = time.perf_counter()

        row["t_read_ms"] = (t1 - t0) * 1000
        row["t_proc_ms"] = (t2 - t1) * 1000
        row["t_write_ms"] = (t3 - t2) * 1000
        row["ok"] = 1

    except Exception as e:
        row["err"] = str(e)

    return row


def write_csv(path, rows):
    """Write a list of dict rows to CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def append_timing(path, timing_row):
    """Append one timing row into timings_all.csv."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(timing_row.keys()))
        if not exists:
            w.writeheader()
        w.writerow(timing_row)


def main():
    ap = argparse.ArgumentParser(description="Batch image processing (sequential + parallel)")
    ap.add_argument("--in", dest="inp", required=True, help="Input folder (e.g. input_small)")
    ap.add_argument("--out", dest="out", required=True, help="Output folder base (e.g. output)")
    ap.add_argument("--mode", choices=["seq", "par"], required=True, help="seq or par")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="Workers for parallel mode")
    ap.add_argument("--runs", type=int, default=3, help="Repeat runs for benchmarking")
    ap.add_argument("--ops", nargs="+", default=["resize:800x600", "gray", "blur:1.2"])
    ap.add_argument("--fmt", default="jpg", help="Output format extension (jpg or png recommended)")
    ap.add_argument("--quality", type=int, default=85, help="JPEG quality (only used for jpg)")
    args = ap.parse_args()

    # Hardware proof / info
    print("CPU logical processors:", os.cpu_count())

    files = list_images(args.inp)
    if not files:
        print("No images found in input folder:", args.inp)
        return

    dataset = Path(args.inp).name
    workers_used = args.workers if args.mode == "par" else 1

    print(f"Dataset={dataset} Files={len(files)} Mode={args.mode} Workers={workers_used}")
    print(f"Ops={args.ops} Format={args.fmt}")

    for run_i in range(1, args.runs + 1):
        run_out = Path(args.out) / dataset / f"{args.mode}_w{workers_used}" / f"run{run_i}"
        run_out.mkdir(parents=True, exist_ok=True)

        # Build job list: one job per image
        jobs = []
        for f in files:
            jobs.append((str(f), args.inp, str(run_out), args.ops, args.fmt, args.quality))

        t0 = time.perf_counter()

        if args.mode == "seq":
            rows = [process_one(job) for job in jobs]

        elif args.mode == "par":
            with ProcessPoolExecutor(max_workers=args.workers) as ex:
                rows = list(ex.map(process_one, jobs))

        else:
            raise ValueError("Invalid mode: " + str(args.mode))

        t1 = time.perf_counter()
        secs = t1 - t0

        # Write per-image results
        write_csv(run_out / "results.csv", rows)

        # Append timing summary row
        append_timing(
            Path(args.out) / "timings_all.csv",
            {
                "dataset": dataset,
                "files": len(files),
                "mode": args.mode,
                "workers": workers_used,
                "run": run_i,
                "seconds": f"{secs:.6f}",
                "ops": " ".join(args.ops),
                "fmt": args.fmt,
            }
        )

        ok_count = sum(1 for r in rows if r["ok"] == 1)
        print(f"  Run {run_i}: {secs:.3f}s | ok={ok_count}/{len(rows)} | {run_out}")


if __name__ == "__main__":
    main()