"""Bagian bersama skrip eksperimen yang bisa dilanjutkan (05_runner.py, 08_ortools.py)."""
import csv
import time
from functools import lru_cache
from multiprocessing import Pool

import numpy as np


@lru_cache(maxsize=None)
def muat_matriks(merek):
    """Matriks jarak data/matriks_<merek>.npy, dimuat sekali per proses."""
    return np.load(f"data/matriks_{merek}.npy")


def sudah_selesai(path):
    """Kunci (merek, gudang, n, skenario) yang sudah ada di file CSV hasil."""
    if not path.exists():
        return set()
    with open(path, newline="") as f:
        return {(r["merek"], int(r["gudang"]), int(r["n"]), int(r["skenario"]))
                for r in csv.DictReader(f)}


def jalankan_dan_tulis(path, tugas, kerjakan, kolom, proses):
    """Kerjakan tugas paralel dan tulis tiap hasil langsung ke CSV (bisa dilanjutkan bila terhenti)."""
    total = len(tugas)
    baru = not path.exists()
    mulai = time.time()
    with open(path, "a", newline="") as f, Pool(proses) as pool:
        w = csv.DictWriter(f, fieldnames=kolom)
        if baru:
            w.writeheader()
        for i, baris in enumerate(pool.imap_unordered(kerjakan, tugas), 1):
            w.writerow(baris)
            f.flush()
            if i % 10 == 0 or i == total:
                lalu = time.time() - mulai
                print(f"  {i}/{total}  berlalu {lalu/60:.1f} mnt, sisa sekitar "
                      f"{lalu / i * (total - i) / 60:.1f} mnt")
