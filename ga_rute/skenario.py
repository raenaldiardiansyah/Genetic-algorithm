"""Pembuatan skenario pengiriman (toko acak di sekitar gudang, seed tetap)."""
import numpy as np


def toko_dalam_zona(D, idx_gudang, idx_toko, radius_km):
    """Toko yang jarak jalannya ke/dari gudang <= radius_km."""
    return [j for j in idx_toko
            if min(D[idx_gudang, j], D[j, idx_gudang]) <= radius_km]


def seed_skenario(no_gudang, n_toko, k):
    """Seed unik dan tetap untuk setiap skenario (supaya bisa diulang)."""
    return no_gudang * 100_000 + n_toko * 1_000 + k


def buat_skenario(zona, n_toko, seed):
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(np.asarray(zona), size=n_toko, replace=False))


def submatriks(D, idx_gudang, toko):
    """Matriks (N+1)x(N+1) dengan gudang di indeks 0, siap dipakai GA."""
    idx = [idx_gudang] + list(toko)
    return D[np.ix_(idx, idx)]


def skenario_ke(D, g, n, k):
    """Skenario ke-k untuk gudang g (0-based) dan n toko. Satu resep untuk semua skrip.

    Kembalikan (Ds, toko, seed): submatriks siap GA, indeks toko di D, dan seed skenario.
    """
    from ga_rute import konfig
    zona = toko_dalam_zona(D, g, range(konfig.JUMLAH_GUDANG, D.shape[0]), konfig.RADIUS_KM)
    if len(zona) < n:
        raise ValueError(f"Zona gudang {g + 1} hanya {len(zona)} toko, kurang dari N={n}. "
                         "Naikkan RADIUS_KM di ga_rute/konfig.py.")
    seed = seed_skenario(g + 1, n, k)
    toko = buat_skenario(zona, n, seed)
    return submatriks(D, g, toko), toko, seed
