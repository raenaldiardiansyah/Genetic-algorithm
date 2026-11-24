import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd
from ga_rute.skenario import toko_dalam_zona

gudang = pd.read_csv("data/gudang.csv")
for merek in ("indomaret", "alfamart"):
    D = np.load(f"data/matriks_{merek}.npy")
    idx = list(range(len(gudang), D.shape[0]))
    print(f"\n{merek}: jumlah toko dalam zona")
    print("radius_km | " + " | ".join(f"gudang {i+1}" for i in range(len(gudang))))
    for r in (6, 8, 10, 12, 14, 16, 20):
        jml = [len(toko_dalam_zona(D, k, idx, r)) for k in range(len(gudang))]
        print(f"{r:>9} | " + " | ".join(f"{j:>8}" for j in jml))