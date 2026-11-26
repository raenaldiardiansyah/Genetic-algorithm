"""Visualisasi satu skenario: peta rute di jalan asli, grafik konvergensi, dan GIF per generasi.

    python scripts/11_visualisasi.py --merek indomaret --gudang 1 --n 10 --k 1
    python scripts/11_visualisasi.py --n 20 --tanpa-gif

Keluaran di folder hasil/ (png dan gif). Butuh data/jalan_bandung.graphml dari 01_unduh_osm.py.
"""
import sys, os, pathlib, argparse
RAKIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAKIT))
os.chdir(RAKIT)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import osmnx as ox
from ga_rute import konfig
from ga_rute.data import simpul_terdekat
from ga_rute.ga import jalankan_ga, panjang_rute
from ga_rute.baselines import nearest_neighbor, held_karp
from ga_rute.skenario import skenario_ke
from ga_rute.visual import jalur_rute, pilih_bingkai

WARNA_JALAN, WARNA_GA, WARNA_NN = "#c9ced8", "#14213d", "#d1495b"


def siapkan_peta(ax, tepi, kotak, titik_x, titik_y, kode):
    x0, x1, y0, y1 = kotak
    tepi.cx[x0:x1, y0:y1].plot(ax=ax, color=WARNA_JALAN, linewidth=0.6, zorder=1)
    ax.scatter(titik_x[1:], titik_y[1:], s=55, color="#e8833a", edgecolor="white", zorder=4)
    ax.scatter(titik_x[:1], titik_y[:1], s=130, marker="s", color="#2a7471", edgecolor="white", zorder=5)
    for i in range(1, len(titik_x)):
        ax.annotate(kode[i], (titik_x[i], titik_y[i]), xytext=(4, 4), textcoords="offset points",
                    fontsize=7, zorder=6)
    ax.annotate("G", (titik_x[0], titik_y[0]), xytext=(5, 5), textcoords="offset points",
                fontsize=9, fontweight="bold", zorder=6)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect(1 / np.cos(np.radians((y0 + y1) / 2)))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merek", default="indomaret", choices=["indomaret", "alfamart"])
    ap.add_argument("--gudang", type=int, default=1, choices=[1, 2, 3])
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--bingkai", type=int, default=30, help="jumlah bingkai GIF")
    ap.add_argument("--tanpa-gif", action="store_true")
    a = ap.parse_args()
    os.makedirs("hasil", exist_ok=True)
    nama = f"{a.merek}_g{a.gudang}_n{a.n}_k{a.k}"

    print("Memuat graf jalan ...")
    G = ox.load_graphml("data/jalan_bandung.graphml")
    D = np.load(f"data/matriks_{a.merek}.npy")
    gudang = pd.read_csv("data/gudang.csv")
    toko_csv = pd.read_csv(f"data/{a.merek}.csv")
    n_gudang = konfig.JUMLAH_GUDANG

    g = a.gudang - 1
    Ds, toko, seed = skenario_ke(D, g, a.n, a.k)
    kode = ["G"] + [f"T{i}" for i in range(1, a.n + 1)]

    lon = np.concatenate([[gudang["lon"].iloc[g]], toko_csv["lon"].values[toko - n_gudang]])
    lat = np.concatenate([[gudang["lat"].iloc[g]], toko_csv["lat"].values[toko - n_gudang]])
    simpul, _ = simpul_terdekat(G, lon, lat)

    print("Menjalankan nearest neighbor dan GA ...")
    rute_nn, km_nn = nearest_neighbor(Ds)
    km_hk = held_karp(Ds)[1] if a.n <= 12 else None
    bingkai = set(pilih_bingkai(konfig.GENERASI, a.bingkai))
    rekam = {}

    def catat(gen, rute, km):
        if gen in bingkai:
            rekam[gen] = (rute, km)

    rute_ga, km_ga, riwayat = jalankan_ga(Ds, konfig.UKURAN_POP, konfig.GENERASI, seed=seed,
                                          callback=catat)
    print(f"NN {km_nn:.3f} km | GA {km_ga:.3f} km" + (f" | optimum {km_hk:.3f} km" if km_hk else ""))

    # ---- batas peta: sekitar titik + jalur yang dilalui ----
    cache = {}
    xs_ga, ys_ga = jalur_rute(G, simpul, rute_ga, cache)
    xs_nn, ys_nn = jalur_rute(G, simpul, rute_nn, cache)
    semua_x = np.concatenate([xs_ga, xs_nn, lon])
    semua_y = np.concatenate([ys_ga, ys_nn, lat])
    mx = max(0.08 * np.ptp(semua_x), 0.003)
    my = max(0.08 * np.ptp(semua_y), 0.003)
    kotak = (semua_x.min() - mx, semua_x.max() + mx, semua_y.min() - my, semua_y.max() + my)
    tepi = ox.graph_to_gdfs(G, nodes=False)

    # ---- 1. peta NN vs GA ----
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5))
    for ax, (xs, ys), warna, judul in (
            (axes[0], (xs_nn, ys_nn), WARNA_NN, f"Nearest neighbor: {km_nn:.2f} km"),
            (axes[1], (xs_ga, ys_ga), WARNA_GA, f"Algoritma Genetika: {km_ga:.2f} km")):
        siapkan_peta(ax, tepi, kotak, lon, lat, kode)
        ax.plot(xs, ys, color=warna, linewidth=2.2, alpha=0.9, zorder=3)
        ax.set_title(judul)
    hemat = 100 * (km_nn - km_ga) / km_nn
    banding = (f"GA {abs(hemat):.1f}% lebih pendek dari nearest neighbor" if hemat > 0.05 else
               f"GA {abs(hemat):.1f}% lebih panjang dari nearest neighbor" if hemat < -0.05 else
               "GA sama dengan nearest neighbor")
    fig.suptitle(f"{a.merek.capitalize()}, gudang {a.gudang}, {a.n} gerai, skenario {a.k}   ({banding})")
    fig.tight_layout()
    f1 = f"hasil/peta_{nama}.png"
    fig.savefig(f1, dpi=150)
    plt.close(fig)

    # ---- 2. konvergensi ----
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(riwayat, color=WARNA_GA, label="GA: rute terbaik per generasi")
    ax.axhline(km_nn, color=WARNA_NN, linestyle=":", label="nearest neighbor")
    if km_hk:
        ax.axhline(km_hk, color="#2a7471", linestyle="--", label="optimum (Held-Karp)")
    ax.set_xlabel("Generasi")
    ax.set_ylabel("Panjang rute (km)")
    ax.set_title(f"Konvergensi GA ({a.merek}, gudang {a.gudang}, {a.n} gerai)")
    ax.legend()
    fig.tight_layout()
    f2 = f"hasil/konvergensi_{nama}.png"
    fig.savefig(f2, dpi=150)
    plt.close(fig)
    print("Disimpan:", f1, "|", f2)

    # ---- 3. GIF per generasi ----
    if not a.tanpa_gif:
        urut_gen = sorted(rekam)
        fig, ax = plt.subplots(figsize=(6.5, 6.5))
        siapkan_peta(ax, tepi, kotak, lon, lat, kode)
        garis, = ax.plot([], [], color=WARNA_GA, linewidth=2.2, alpha=0.9, zorder=3)
        judul = ax.set_title("")

        def gambar(i):
            gen = urut_gen[i]
            rute, km = rekam[gen]
            xs, ys = jalur_rute(G, simpul, rute, cache)
            garis.set_data(xs, ys)
            judul.set_text(f"Generasi {gen + 1}: {km:.2f} km")
            return garis, judul

        anim = FuncAnimation(fig, gambar, frames=len(urut_gen), blit=False)
        f3 = f"hasil/ga_{nama}.gif"
        print(f"Membuat GIF ({len(urut_gen)} bingkai) ...")
        anim.save(f3, writer=PillowWriter(fps=3), dpi=80)
        plt.close(fig)
        print("Disimpan:", f3)


if __name__ == "__main__":
    main()
