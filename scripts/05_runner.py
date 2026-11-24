"""Langkah 4: jalankan GA, nearest neighbor (dan Held-Karp untuk 10 toko)
pada semua skenario. Memakai banyak core CPU dan bisa DILANJUTKAN: hasil ditulis
per skenario ke hasil/hasil_<merek>.csv, skenario yang sudah ada dilewati.

Contoh:
    python scripts/05_runner.py --merek indomaret --jumlah 2     # uji cepat
    python scripts/05_runner.py --merek semua                    # eksperimen penuh
"""
import sys, os, pathlib, time, argparse, csv
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)

import numpy as np
from multiprocessing import Pool
from ga_rute import konfig
from ga_rute.ga import jalankan_ga
from ga_rute.baselines import nearest_neighbor, held_karp
from ga_rute.skenario import (toko_dalam_zona, buat_skenario, submatriks,
                              seed_skenario)

KOLOM = ["merek", "gudang", "n", "skenario", "seed", "ga_km", "nn_km", "hk_km",
         "waktu_ga_s", "rute_ga"]
_CACHE = {}


def _muat(merek):
    if merek not in _CACHE:
        _CACHE[merek] = np.load(f"data/matriks_{merek}.npy")
    return _CACHE[merek]


def kerjakan(tugas):
    merek, g, n, k, lokal = tugas
    D = _muat(merek)
    n_gudang = konfig.JUMLAH_GUDANG
    zona = toko_dalam_zona(D, g, range(n_gudang, D.shape[0]), konfig.RADIUS_KM)
    if len(zona) < n:
        raise ValueError(f"Zona {merek} gudang {g + 1} hanya {len(zona)} toko, kurang dari "
                         f"N={n}. Naikkan RADIUS_KM di ga_rute/konfig.py.")
    seed = seed_skenario(g + 1, n, k)
    toko = buat_skenario(zona, n, seed)
    Ds = submatriks(D, g, toko)
    t = time.time()
    rute, ga_km, _ = jalankan_ga(Ds, konfig.UKURAN_POP, konfig.GENERASI, seed=seed,
                                 lokal=lokal)
    waktu = time.time() - t
    _, nn_km = nearest_neighbor(Ds)
    hk_km = round(held_karp(Ds)[1], 4) if n <= 10 else ""
    urutan = toko[rute - 1] - n_gudang      # nomor baris di data/<merek>.csv
    return dict(merek=merek, gudang=g + 1, n=n, skenario=k, seed=seed,
                ga_km=round(ga_km, 4), nn_km=round(nn_km, 4), hk_km=hk_km,
                waktu_ga_s=round(waktu, 2), rute_ga=" ".join(map(str, urutan)))


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
    ap.add_argument("--proses", type=int, default=os.cpu_count())
    ap.add_argument("--lokal", default="none", choices=["none", "akhir"],
                    help="akhir = GA + 2-opt pada hasil akhir (hasil di file *_2opt.csv)")
    a = ap.parse_args()
    merek_list = ["indomaret", "alfamart"] if a.merek == "semua" else [a.merek]
    os.makedirs("hasil", exist_ok=True)

    for merek in merek_list:
        sufiks = "" if a.lokal == "none" else "_2opt"
        path = pathlib.Path(f"hasil/hasil_{merek}{sufiks}.csv")
        lokal = None if a.lokal == "none" else a.lokal
        selesai = sudah_selesai(path)
        tugas = [(merek, g, n, k, lokal)
                 for g in range(konfig.JUMLAH_GUDANG)
                 for n in konfig.UKURAN
                 for k in range(1, a.jumlah + 1)
                 if (merek, g + 1, n, k) not in selesai]
        total = len(tugas)
        print(f"\n[{merek}] {len(selesai)} sudah selesai, {total} tersisa, {a.proses} proses")
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
                    sisa = lalu / i * (total - i)
                    print(f"  {i}/{total}  berlalu {lalu/60:.1f} mnt, sisa sekitar {sisa/60:.1f} mnt")
    print("\nSelesai. Hasil ada di folder hasil/.")


if __name__ == "__main__":
    main()
