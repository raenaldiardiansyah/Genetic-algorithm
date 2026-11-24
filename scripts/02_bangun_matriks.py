"""Langkah 2b: bangun matriks jarak jalan (Dijkstra) dari data hasil 01_unduh_osm.py."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd
import osmnx as ox
from ga_rute import data
from ga_rute.skenario import toko_dalam_zona
from ga_rute.konfig import RADIUS_KM

G = ox.load_graphml("data/jalan_bandung.graphml")
gudang = pd.read_csv("data/gudang.csv")
print("Gudang yang dipakai (PASTIKAN koordinatnya masuk akal di peta):")
print(gudang.to_string(index=False))

for merek in ("indomaret", "alfamart"):
    toko = pd.read_csv(f"data/{merek}.csv")
    lon = np.concatenate([gudang["lon"].values, toko["lon"].values])
    lat = np.concatenate([gudang["lat"].values, toko["lat"].values])
    D, simpul, snap = data.bangun_matriks(G, lon, lat)
    np.save(f"data/matriks_{merek}.npy", D)
    print(f"\n[{merek}] matriks {D.shape}, semua terhingga: {np.isfinite(D).all()}")
    print(f"  jarak snap titik ke simpul jalan: median {np.median(snap):.0f} m, maks {snap.max():.0f} m")
    asim = np.abs(D - D.T).max()
    print(f"  selisih terbesar jarak A->B vs B->A: {asim:.2f} km (asimetris = jalan satu arah)")
    idx_toko = list(range(len(gudang), len(gudang) + len(toko)))
    for g in range(len(gudang)):
        zona = toko_dalam_zona(D, g, idx_toko, RADIUS_KM)
        status = "OK" if len(zona) >= 40 else "KURANG, naikkan RADIUS_KM"
        print(f"  gudang {g+1}: {len(zona)} toko dalam {RADIUS_KM} km  -> {status}")
