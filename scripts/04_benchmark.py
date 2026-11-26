import sys, pathlib, time, os
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)
import numpy as np
from ga_rute.ga import jalankan_ga
from ga_rute.skenario import (toko_dalam_zona, buat_skenario,
                              submatriks, seed_skenario)

print("Jumlah core CPU:", os.cpu_count())
D = np.load("data/matriks_indomaret.npy")
idx = list(range(3, D.shape[0]))
zona = toko_dalam_zona(D, 0, idx, 10)
for n in (10, 20, 30):
    toko = buat_skenario(zona, n, seed_skenario(1, n, 1))
    t = time.time()
    _, hasil, _ = jalankan_ga(submatriks(D, 0, toko), 100, 1000, seed=1)
    print(n, "toko:", round(hasil, 2), "km,", round(time.time() - t, 1), "detik")