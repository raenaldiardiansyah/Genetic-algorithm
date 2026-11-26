"""Eksperimen parameter GA pada skenario TERPISAH (k = 101..), anggaran sama 100.000 evaluasi.
Satu faktor diubah sekali waktu dari konfigurasi dasar; patokan = OR-Tools.

    python scripts/09_eksperimen_parameter.py --merek indomaret --n 30
    python scripts/09_eksperimen_parameter.py --jumlah 2 --seeds 1 --n 20     # uji cepat
"""
import sys, os, pathlib, argparse, time, csv
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)
import numpy as np
import pandas as pd
from multiprocessing import Pool
from ga_rute import konfig
from ga_rute.ga import jalankan_ga
from ga_rute.baselines import ortools_atsp
from ga_rute.skenario import skenario_ke

ANGGARAN = 100_000
DASAR = dict(pop=100, mut=0.2, crossover="ox", seleksi="turnamen", lokal=None)
KONFIG = {"dasar": {}}
for p in (50, 200):
    KONFIG[f"pop={p}"] = dict(pop=p)
for m in (0.02, 0.05, 0.1, 0.5):
    KONFIG[f"mutasi={m}"] = dict(mut=m)
KONFIG["PMX"] = dict(crossover="pmx")
KONFIG["rank"] = dict(seleksi="rank")
KONFIG["+2opt"] = dict(lokal="akhir")
_CACHE = {}


def _skenario(merek, n, k):
    if merek not in _CACHE:
        _CACHE[merek] = np.load(f"data/matriks_{merek}.npy")
    g = (k - 1) % konfig.JUMLAH_GUDANG                  # gudang bergilir
    Ds, _, seed = skenario_ke(_CACHE[merek], g, n, k)
    return Ds, seed, g + 1


def kerjakan(arg):
    merek, n, k, nama, seed_ke, detik = arg
    Ds, seed, gudang = _skenario(merek, n, k)
    if nama == "OR-Tools":
        return dict(konfig=nama, skenario=k, gudang=gudang, seed_ke=0,
                    km=ortools_atsp(Ds, detik)[1], detik=0.0)
    c = {**DASAR, **KONFIG[nama]}
    t = time.time()
    _, km, _ = jalankan_ga(Ds, c["pop"], ANGGARAN // c["pop"], p_mut=c["mut"],
                           crossover=c["crossover"], seleksi=c["seleksi"], lokal=c["lokal"],
                           seed=seed + 7919 * seed_ke)
    return dict(konfig=nama, skenario=k, gudang=gudang, seed_ke=seed_ke, km=km,
                detik=time.time() - t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merek", default="indomaret", choices=["indomaret", "alfamart"])
    ap.add_argument("--n", type=int, default=30, choices=[10, 20, 30])
    ap.add_argument("--jumlah", type=int, default=20, help="jumlah skenario penyetelan")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--detik", type=int, default=2, help="batas waktu OR-Tools")
    ap.add_argument("--proses", type=int, default=os.cpu_count())
    a = ap.parse_args()
    ks = range(101, 101 + a.jumlah)
    tugas = [(a.merek, a.n, k, "OR-Tools", 0, a.detik) for k in ks]
    tugas += [(a.merek, a.n, k, nama, s, a.detik)
              for nama in KONFIG for k in ks for s in range(a.seeds)]
    print(f"{len(tugas)} proses ({len(KONFIG)} konfigurasi x {a.jumlah} skenario x {a.seeds} seed "
          f"+ OR-Tools), {a.proses} core")
    mulai = time.time()
    with Pool(a.proses) as pool:
        baris = pool.map(kerjakan, tugas, chunksize=1)
    df = pd.DataFrame(baris)
    os.makedirs("hasil", exist_ok=True)
    df.to_csv(f"hasil/parameter_{a.merek}_n{a.n}.csv", index=False)

    ref = df[df.konfig == "OR-Tools"].set_index("skenario")["km"]
    ga = df[df.konfig != "OR-Tools"].copy()
    ga["gap_pct"] = 100 * (ga["km"] - ga["skenario"].map(ref)) / ga["skenario"].map(ref)
    per_skenario = ga.groupby(["konfig", "skenario"])["gap_pct"].mean().unstack(0)   # rata2 antar seed
    dasar = per_skenario["dasar"]
    baris = []
    for nama in KONFIG:
        x = per_skenario[nama]
        baris.append(dict(konfigurasi=nama, gap_rata_pct=x.mean(), gap_median_pct=x.median(),
                          gap_std_antar_skenario=x.std(),
                          lebih_baik_dari_dasar_pct=100 * float((x < dasar - 1e-9).mean()) if nama != "dasar" else np.nan,
                          detik_per_run=ga[ga.konfig == nama]["detik"].mean()))
    ring = pd.DataFrame(baris).sort_values("gap_rata_pct")
    pd.set_option("display.width", 200)
    print(f"\n=== Gap GA ke OR-Tools, {a.merek}, {a.n} toko, {a.jumlah} skenario penyetelan, "
          f"rata-rata {a.seeds} seed ===")
    print(ring.round(3).to_string(index=False))
    ring.round(4).to_csv(f"hasil/ringkasan_parameter_{a.merek}_n{a.n}.csv", index=False)
    print(f"\nTotal waktu {(time.time() - mulai) / 60:.1f} menit")


if __name__ == "__main__":
    main()
