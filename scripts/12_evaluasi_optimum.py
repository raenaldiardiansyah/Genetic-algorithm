"""Evaluasi sampai optimum (10 toko): berapa individu dievaluasi GA sampai rute
terbaiknya pertama kali sama dengan optimum Held-Karp.

Skenario dan seed sama dengan 05_runner.py, jadi ga_km harus sama dengan
hasil/hasil_<merek>.csv (dicek di akhir).

Hitungan evaluasi: populasi awal (UKURAN_POP) + (UKURAN_POP - 2 elit) individu baru
per generasi. Run yang tidak pernah mencapai optimum diberi -1.

    python scripts/12_evaluasi_optimum.py
"""
import sys, os, pathlib
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)

import numpy as np
import pandas as pd
from multiprocessing import Pool
from ga_rute import konfig
from ga_rute.ga import jalankan_ga, generasi_capai
from ga_rute.baselines import held_karp
from ga_rute.skenario import skenario_ke

N = 10
N_ELIT = 2


def kerjakan(tugas):
    merek, g, k = tugas
    D = np.load(f"data/matriks_{merek}.npy")
    Ds, _, seed = skenario_ke(D, g, N, k)
    _, ga_km, riwayat = jalankan_ga(Ds, konfig.UKURAN_POP, konfig.GENERASI, seed=seed)
    hk_km = held_karp(Ds)[1]
    gen = generasi_capai(riwayat, hk_km)
    evaluasi = konfig.UKURAN_POP + gen * (konfig.UKURAN_POP - N_ELIT) if gen >= 0 else -1
    return dict(merek=merek, gudang=g + 1, n=N, skenario=k, seed=seed,
                ga_km=round(ga_km, 4), hk_km=round(hk_km, 4),
                generasi_optimum=gen, evaluasi_optimum=evaluasi)


def main():
    tugas = [(m, g, k) for m in ("indomaret", "alfamart")
             for g in range(konfig.JUMLAH_GUDANG)
             for k in range(1, konfig.JUMLAH_SKENARIO + 1)]
    with Pool(os.cpu_count()) as pool:
        df = pd.DataFrame(pool.map(kerjakan, tugas))
    df.to_csv("hasil/evaluasi_optimum.csv", index=False)

    # cek: hasil GA harus sama dengan eksperimen utama
    lama = pd.concat([pd.read_csv(f"hasil/hasil_{m}.csv") for m in ("indomaret", "alfamart")])
    cek = df.merge(lama[lama.n == N], on=["merek", "gudang", "n", "skenario"], suffixes=("", "_lama"))
    beda = int((np.abs(cek.ga_km - cek.ga_km_lama) > 1e-3).sum())
    print(f"Cocok dengan hasil_<merek>.csv: {len(cek) - beda}/{len(cek)} skenario")

    capai = df[df.evaluasi_optimum >= 0]
    ring = df.groupby(["merek", "gudang"]).agg(
        jumlah=("skenario", "size"),
        sukses_pct=("evaluasi_optimum", lambda s: 100 * float((s >= 0).mean()))).reset_index()
    ev = capai.groupby(["merek", "gudang"]).evaluasi_optimum.agg(
        evaluasi_median="median", evaluasi_rata="mean", evaluasi_maks="max").reset_index()
    ring = ring.merge(ev, on=["merek", "gudang"], how="left")
    print(ring.round(1).to_string(index=False))
    ring.round(1).to_csv("hasil/ringkasan_evaluasi_optimum.csv", index=False)


if __name__ == "__main__":
    main()
