"""Validasi GA pada soal TSPLIB (kroA100, ftv33, ftv70): gap ke optimum resmi.

Taruh file di data/tsplib/ (misalnya kroA100.tsp, ftv33.atsp, ftv70.atsp), lalu:
    python scripts/10_tsplib.py
    python scripts/10_tsplib.py --seeds 10 --lokal akhir
"""
import sys, os, pathlib, argparse, time
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)
import numpy as np
from multiprocessing import Pool
from ga_rute import konfig
from ga_rute.ga import jalankan_ga
from ga_rute.tsplib import baca_tsplib, OPTIMUM


def satu_run(arg):
    path, seed, lokal = arg
    D = baca_tsplib(path)
    t = time.time()
    _, km, _ = jalankan_ga(D, konfig.UKURAN_POP, konfig.GENERASI, seed=seed, lokal=lokal)
    return km, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default="data/tsplib")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--lokal", default="none", choices=["none", "akhir"])
    ap.add_argument("--proses", type=int, default=os.cpu_count())
    a = ap.parse_args()
    lokal = None if a.lokal == "none" else a.lokal
    berkas = sorted(p for p in pathlib.Path(a.folder).glob("*") if p.suffix in (".tsp", ".atsp"))
    if not berkas:
        sys.exit(f"Tidak ada file .tsp/.atsp di {a.folder}")
    print(f"GA: populasi {konfig.UKURAN_POP}, {konfig.GENERASI} generasi, {a.seeds} seed, lokal={a.lokal}\n")
    print(f"{'soal':10} {'optimum':>8} {'terbaik':>9} {'rata2':>9} {'gap_min%':>9} {'gap_rata%':>10} {'gap_maks%':>10} {'optimal':>8}")
    with Pool(a.proses) as pool:
        for p in berkas:
            nama = p.stem
            hasil = pool.map(satu_run, [(str(p), s, lokal) for s in range(a.seeds)])
            km = np.array([h[0] for h in hasil])
            opt = OPTIMUM.get(nama)
            if opt is None:
                print(f"{nama:10} (optimum tidak diketahui) terbaik {km.min():.0f} rata2 {km.mean():.1f}")
                continue
            gap = 100 * (km - opt) / opt
            print(f"{nama:10} {opt:8d} {km.min():9.0f} {km.mean():9.1f} {gap.min():9.2f} "
                  f"{gap.mean():10.2f} {gap.max():10.2f} {(km <= opt + 1e-9).sum():>5}/{a.seeds}")


if __name__ == "__main__":
    main()
