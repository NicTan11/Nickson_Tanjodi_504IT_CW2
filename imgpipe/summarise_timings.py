import csv
import statistics
from pathlib import Path

def main():
    timings_path = Path("output") / "timings_all.csv"
    if not timings_path.exists():
        print("Missing:", timings_path)
        return

    # de-duplicate by (dataset, mode, workers, run)
    latest = {}
    with timings_path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k = (row["dataset"], row["mode"], int(row["workers"]), int(row["run"]))
            latest[k] = row

    groups = {}
    files_map = {}

    for row in latest.values():
        ds = row["dataset"]
        md = row["mode"]
        wk = int(row["workers"])
        sec = float(row["seconds"])

        groups.setdefault((ds, md, wk), []).append(sec)
        files_map[ds] = int(row["files"])

    baseline = {}
    for (ds, md, wk), secs in groups.items():
        if md == "seq" and wk == 1:
            baseline[ds] = statistics.mean(secs)

    out_path = Path("output") / "summary_table.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dataset","files","mode","workers","runs","mean_s","std_s","speedup_vs_seq"])

        for (ds, md, wk) in sorted(groups.keys()):
            secs = groups[(ds, md, wk)]
            mean_s = statistics.mean(secs)
            std_s = statistics.pstdev(secs) if len(secs) > 1 else 0.0
            speedup = baseline[ds] / mean_s if ds in baseline else 1.0
            w.writerow([ds, files_map[ds], md, wk, len(secs), f"{mean_s:.6f}", f"{std_s:.6f}", f"{speedup:.6f}"])

    print("Wrote:", out_path)

    # readable printout
    print("\n===== SUMMARY =====")
    datasets = sorted(set(ds for (ds, _, _) in groups.keys()))
    for ds in datasets:
        print(f"\nDataset: {ds} (files={files_map[ds]})")
        print("mode  workers   mean_s   std_s   speedup")
        for (md, wk) in [("seq", 1), ("par", 2), ("par", 4), ("par", 8)]:
            k = (ds, md, wk)
            if k not in groups:
                continue
            secs = groups[k]
            mean_s = statistics.mean(secs)
            std_s = statistics.pstdev(secs) if len(secs) > 1 else 0.0
            speedup = baseline[ds] / mean_s
            print(f"{md:<4}  {wk:>7}  {mean_s:>6.3f}  {std_s:>6.3f}  {speedup:>7.2f}x")

if __name__ == "__main__":
    main()