import csv
import statistics
from pathlib import Path


def main():
    timings_path = Path("output") / "timings_all.csv"
    if not timings_path.exists():
        print("Missing:", timings_path)
        return

    # Read + de-duplicate by (dataset, mode, workers, run) (case-insensitive dataset key)
    latest = {}
    with timings_path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ds_raw = row["dataset"].strip()
            ds_key = ds_raw.lower()  # normalize case

            md = row["mode"].strip()
            wk = int(row["workers"])
            rn = int(row["run"])

            k = (ds_key, md, wk, rn)
            # keep the last occurrence if duplicates exist
            row["_dataset_key"] = ds_key
            latest[k] = row

    # Group seconds by (dataset_key, mode, workers)
    groups = {}
    files_map = {}
    display_name = {}  # dataset_key -> original dataset string (first seen)

    for row in latest.values():
        ds_key = row["_dataset_key"]
        ds_raw = row["dataset"].strip()
        md = row["mode"].strip()
        wk = int(row["workers"])
        sec = float(row["seconds"])

        display_name.setdefault(ds_key, ds_raw)
        files_map[ds_key] = int(row["files"])

        gk = (ds_key, md, wk)
        groups.setdefault(gk, []).append(sec)

    # Baseline per dataset (seq, workers=1)
    baseline = {}
    for (ds_key, md, wk), secs in groups.items():
        if md == "seq" and wk == 1:
            baseline[ds_key] = statistics.mean(secs)

    # Write summary CSV (speedup blank if no baseline)
    out_path = Path("output") / "summary_table.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "files", "mode", "workers", "runs", "mean_s", "std_s", "speedup_vs_seq"])

        for (ds_key, md, wk) in sorted(groups.keys()):
            secs = groups[(ds_key, md, wk)]
            mean_s = statistics.mean(secs)
            std_s = statistics.pstdev(secs) if len(secs) > 1 else 0.0

            if ds_key in baseline:
                speedup = baseline[ds_key] / mean_s
                speedup_str = f"{speedup:.6f}"
            else:
                speedup_str = ""  # blank = no seq baseline available

            w.writerow([
                display_name.get(ds_key, ds_key),
                files_map.get(ds_key, ""),
                md,
                wk,
                len(secs),
                f"{mean_s:.6f}",
                f"{std_s:.6f}",
                speedup_str
            ])

    print("Wrote:", out_path)

    # Print readable summary
    print("\n===== SUMMARY =====")
    for ds_key in sorted(display_name.keys()):
        ds_label = display_name[ds_key]
        print(f"\nDataset: {ds_label} (files={files_map.get(ds_key, '?')})")
        print("mode  workers   mean_s   std_s   speedup")

        # Build a sorted list of workers seen for this dataset
        seen_workers = sorted(set(wk for (dsk, md, wk) in groups.keys() if dsk == ds_key and md == "par"))

        # Always print seq first (if exists)
        seq_key = (ds_key, "seq", 1)
        if seq_key in groups:
            secs = groups[seq_key]
            mean_s = statistics.mean(secs)
            std_s = statistics.pstdev(secs) if len(secs) > 1 else 0.0
            speedup_txt = f"{1.00:>7.2f}x" if ds_key in baseline else "   N/A "
            print(f"{'seq':<4}  {1:>7}  {mean_s:>6.3f}  {std_s:>6.3f}  {speedup_txt}")

        # Then print all parallel worker counts that exist (2,4,6,8,...)
        for wk in seen_workers:
            par_key = (ds_key, "par", wk)
            secs = groups[par_key]
            mean_s = statistics.mean(secs)
            std_s = statistics.pstdev(secs) if len(secs) > 1 else 0.0

            if ds_key in baseline:
                speedup = baseline[ds_key] / mean_s
                speedup_txt = f"{speedup:>7.2f}x"
            else:
                speedup_txt = "   N/A "

            print(f"{'par':<4}  {wk:>7}  {mean_s:>6.3f}  {std_s:>6.3f}  {speedup_txt}")


if __name__ == "__main__":
    main()