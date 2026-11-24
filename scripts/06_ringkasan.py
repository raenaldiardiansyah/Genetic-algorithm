"""Ringkasan hasil: GA vs nearest neighbor (Wilcoxon + koreksi Holm) dan gap ke Held-Karp."""
import sys, os, pathlib
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, rankdata


def holm(p):
    p = np.asarray(p, dtype=float)
    urut = np.argsort(p)
    m = len(p)
    hasil = np.empty(m)
    maks = 0.0
    for rank, i in enumerate(urut):
        maks = max(maks, (m - rank) * p[i])
        hasil[i] = min(1.0, maks)
    return hasil


def efek_rank_biserial(d):
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    r = rankdata(np.abs(d))
    plus, minus = r[d > 0].sum(), r[d < 0].sum()
    return (plus - minus) / (plus + minus)


frames = []
for merek in ("indomaret", "alfamart"):
    p = pathlib.Path(f"hasil/hasil_{merek}.csv")
    if p.exists():
        frames.append(pd.read_csv(p))
if not frames:
    sys.exit("Belum ada hasil. Jalankan scripts/05_runner.py dulu.")
df = pd.concat(frames, ignore_index=True)

baris = []
for (merek, gudang, n), g in df.groupby(["merek", "gudang", "n"]):
    d = (g["nn_km"] - g["ga_km"]).values          # > 0 berarti GA lebih pendek
    try:
        p = wilcoxon(d, alternative="greater").pvalue
    except ValueError:                             # semua selisih nol
        p = 1.0
    item = dict(merek=merek, gudang=gudang, n=n, jumlah=len(g),
                ga_rata_km=g["ga_km"].mean(), nn_rata_km=g["nn_km"].mean(),
                hemat_median_pct=float(np.median(100 * d / g["nn_km"].values)),
                ga_lebih_baik_pct=100 * float((d > 1e-9).mean()),
                ga_sama_pct=100 * float((np.abs(d) <= 1e-9).mean()),
                efek_r=efek_rank_biserial(d), p=p)
    if n <= 10 and g["hk_km"].notna().all():
        gap = 100 * (g["ga_km"] - g["hk_km"]) / g["hk_km"]
        item["gap_hk_rata_pct"] = float(gap.mean())
        item["optimal_pct"] = 100 * float((gap <= 1e-6).mean())
    baris.append(item)

ring = pd.DataFrame(baris)
ring["p_holm"] = holm(ring["p"].values)
ring = ring.drop(columns=["p"])
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
print(ring.round(3).to_string(index=False))
ring.round(4).to_csv("hasil/ringkasan.csv", index=False)
print("\nDisimpan di hasil/ringkasan.csv")


# ---------------- tambahan: GA vs OR-Tools (20 dan 30 toko) ----------------
KUNCI = ["merek", "gudang", "n", "skenario"]
orf = [pd.read_csv(f"hasil/ortools_{m}.csv") for m in ("indomaret", "alfamart")
       if pathlib.Path(f"hasil/ortools_{m}.csv").exists()]
if orf:
    gab = df.merge(pd.concat(orf, ignore_index=True)[KUNCI + ["or_km"]], on=KUNCI)
    baris = []
    for (merek, gudang, n), g in gab.groupby(["merek", "gudang", "n"]):
        gap = 100 * (g["ga_km"] - g["or_km"]) / g["or_km"]
        gap_nn = 100 * (g["nn_km"] - g["or_km"]) / g["or_km"]
        d = (g["ga_km"] - g["or_km"]).values
        try:
            p = wilcoxon(d, alternative="two-sided").pvalue
        except ValueError:
            p = 1.0
        baris.append(dict(merek=merek, gudang=gudang, n=n, jumlah=len(g),
                          gap_ga_median_pct=gap.median(), q1=gap.quantile(.25),
                          q3=gap.quantile(.75), gap_ga_maks_pct=gap.max(),
                          gap_nn_median_pct=gap_nn.median(),
                          ga_lebih_baik_dari_or_pct=100 * float((d < -1e-9).mean()), p=p))
    t2 = pd.DataFrame(baris)
    t2["p_holm"] = holm(t2["p"].values)
    t2 = t2.drop(columns=["p"])
    print("\n=== GA vs OR-Tools (gap positif = GA lebih panjang dari OR-Tools) ===")
    print(t2.round(3).to_string(index=False))
    t2.round(4).to_csv("hasil/ringkasan_ortools.csv", index=False)

# ---------------- tambahan: GA murni vs GA + 2-opt ----------------
dua = [pd.read_csv(f"hasil/hasil_{m}_2opt.csv") for m in ("indomaret", "alfamart")
       if pathlib.Path(f"hasil/hasil_{m}_2opt.csv").exists()]
if dua:
    gab = df.merge(pd.concat(dua, ignore_index=True)[KUNCI + ["ga_km"]], on=KUNCI,
                   suffixes=("", "_2opt"))
    gab["perbaikan_pct"] = 100 * (gab["ga_km"] - gab["ga_km_2opt"]) / gab["ga_km"]
    gab["2opt_kalah_dari_nn"] = gab["ga_km_2opt"] > gab["nn_km"] + 1e-9
    gab["ga_kalah_dari_nn"] = gab["ga_km"] > gab["nn_km"] + 1e-9
    t3 = gab.groupby(["merek", "n"]).agg(
        jumlah=("ga_km", "size"), perbaikan_rata_pct=("perbaikan_pct", "mean"),
        perbaikan_maks_pct=("perbaikan_pct", "max"),
        ga_kalah_nn=("ga_kalah_dari_nn", "sum"),
        ga2opt_kalah_nn=("2opt_kalah_dari_nn", "sum")).reset_index()
    print("\n=== GA murni vs GA + 2-opt (pada skenario yang sama) ===")
    print(t3.round(3).to_string(index=False))
    t3.round(4).to_csv("hasil/ringkasan_2opt.csv", index=False)
