"""Demo langkah 1: GA vs NN vs Held-Karp pada matriks jarak sintetis (tanpa OSM)."""
import sys, os, pathlib
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)
import numpy as np
import matplotlib.pyplot as plt
from ga_rute.ga import jalankan_ga
from ga_rute.baselines import nearest_neighbor, held_karp

rng = np.random.default_rng(42)
N = 10
D = rng.uniform(1, 10, size=(N + 1, N + 1))
np.fill_diagonal(D, 0)

_, opt = held_karp(D)
_, nn = nearest_neighbor(D)
rute, ga, riwayat = jalankan_ga(D, ukuran_pop=100, generasi=300, seed=0)

print(f"Held-Karp (optimal): {opt:.2f}")
print(f"Nearest neighbor   : {nn:.2f}")
print(f"GA                 : {ga:.2f}  (gap {100*(ga-opt)/opt:.2f}%)")
print("Rute GA            : G ->", " -> ".join(f"T{t}" for t in rute), "-> G")

plt.plot(riwayat)
plt.axhline(opt, color="green", linestyle="--", label="optimal (Held-Karp)")
plt.xlabel("Generasi")
plt.ylabel("Panjang rute terbaik")
plt.title("Konvergensi GA")
plt.legend()
plt.savefig("hasil/konvergensi_demo.png", dpi=150)
print("Grafik disimpan di hasil/konvergensi_demo.png")
