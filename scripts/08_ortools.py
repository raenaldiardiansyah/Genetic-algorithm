"""Langkah 5: patokan OR-Tools untuk skenario 20 dan 30 toko (skenario SAMA dengan 05_runner).
Hasil ke hasil/ortools_<merek>.csv; bisa dilanjutkan bila terhenti.
Perlu Python 3.12 + paket ortools.

    python scripts/08_ortools.py --merek indomaret --jumlah 2 --detik 2   # uji cepat
    python scripts/08_ortools.py --merek semua                            # penuh
"""
import sys, os, pathlib, time, argparse, csv
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)

import numpy as np
from multiprocessing import Pool
from ga_rute import konfig
from ga_rute.baselines import ortools_atsp
from ga_rute.skenario import (toko_dalam_zona, buat_skenario, submatriks,
                              seed_skenario)

KOLOM = ["merek", "gudang", "n", "skenario", "seed", "or_km", "detik"]
_CACHE = {}
DETIK = 5


def _muat(merek):
    if merek not in _CACHE:
        _CACHE[merek] = np.load(f"data/matriks_{merek}.npy")
    return _CACHE[merek]


def kerjakan(tugas):
    merek, g, n, k, detik = tugas
    D = _muat(merek)
    zona = toko_dalam_zona(D, g, range(konfig.JUMLAH_GUDANG, D.shape[0]), konfig.RADIUS_KM)
    seed = seed_skenario(g + 1, n, k)
    Ds = submatriks(D, g, buat_skenario(zona, n, seed))
    _, km = ortools_atsp(Ds, detik=detik)
    return dict(merek=merek, gudang=g + 1, n=n, skenario=k, seed=seed,
                or_km=round(km, 4), detik=detik)


def sudah_selesai(path):
    if not path.exists():
        return set()
    with open(path, newline="") as f:
        return {(r["merek"], int(r["gudang"]), int(r["n"]), int(r["skenario"]))
                for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merek", default="semua", choices=["indomaret", "alfamart", "semua"])
    ap.add_argument("--jumlah", type=int, default=konfig.JUMLAH_SKENARIO)
    ap.add_argument("--detik", type=int, default=DETIK, help="batas waktu OR-Tools per skenario")
    ap.add_argument("--proses", type=int, default=os.cpu_count())
    a = ap.parse_args()
    merek_list = ["indomaret", "alfamart"] if a.merek == "semua" else [a.merek]
    for merek in merek_list:
        path = pathlib.Path(f"hasil/ortools_{merek}.csv")
        selesai = sudah_selesai(path)
        tugas = [(merek, g, n, k, a.detik)
                 for g in range(konfig.JUMLAH_GUDANG)
                 for n in konfig.UKURAN if n >= 20
                 for k in range(1, a.jumlah + 1)
                 if (merek, g + 1, n, k) not in selesai]
        total = len(tugas)
        print(f"\n[{merek}] {len(selesai)} sudah selesai, {total} tersisa, "
              f"{a.proses} proses, {a.detik} detik/skenario")
        if not total:
            continue
        baru = not path.exists()
        mulai = time.time()
        with open(path, "a", newline="") as f, Pool(a.proses) as pool:
            w = csv.DictWriter(f, fieldnames=KOLOM)
            if baru:
                w.writeheader()
            for i, baris in enumerate(pool.imap_unordered(kerjakan, tugas), 1):
                w.writerow(baris)
                f.flush()
                if i % 10 == 0 or i == total:
                    lalu = time.time() - mulai
                    print(f"  {i}/{total}  berlalu {lalu/60:.1f} mnt, sisa sekitar "
                          f"{lalu / i * (total - i) / 60:.1f} mnt")
    print("\nSelesai.")


if __name__ == "__main__":
    main()
