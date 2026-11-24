"""Pembaca file TSPLIB (.tsp EUC_2D dan .atsp FULL_MATRIX) -> matriks jarak (N+1)x(N+1)."""
import re
import numpy as np

# Nilai optimum resmi (VERIFIKASI ulang dengan file solusi/daftar di situs TSPLIB sebelum dilaporkan)
OPTIMUM = {"kroA100": 21282, "ftv33": 1286, "ftv70": 1950}


def baca_tsplib(path):
    teks = open(path, encoding="utf-8", errors="ignore").read()
    dim = int(re.search(r"DIMENSION\s*:\s*(\d+)", teks).group(1))
    tipe = re.search(r"EDGE_WEIGHT_TYPE\s*:\s*(\w+)", teks).group(1)
    if tipe == "EUC_2D":
        bagian = teks.split("NODE_COORD_SECTION")[1].split("EOF")[0].split()
        xy = np.array(bagian, dtype=float).reshape(-1, 3)[:, 1:]
        selisih = xy[:, None, :] - xy[None, :, :]
        D = np.floor(np.sqrt((selisih ** 2).sum(axis=2)) + 0.5)      # nint, aturan TSPLIB
    elif tipe == "EXPLICIT":
        fmt = re.search(r"EDGE_WEIGHT_FORMAT\s*:\s*(\w+)", teks).group(1)
        if fmt != "FULL_MATRIX":
            raise ValueError(f"EDGE_WEIGHT_FORMAT {fmt} belum didukung (hanya FULL_MATRIX)")
        angka = teks.split("EDGE_WEIGHT_SECTION")[1].split("EOF")[0].split()
        D = np.array(angka[:dim * dim], dtype=float).reshape(dim, dim)
    else:
        raise ValueError(f"EDGE_WEIGHT_TYPE {tipe} belum didukung")
    if D.shape != (dim, dim):
        raise ValueError("Ukuran matriks tidak sesuai DIMENSION")
    np.fill_diagonal(D, 0)      # diagonal tidak pernah dipakai; hindari nilai besar di file ATSP
    return D
