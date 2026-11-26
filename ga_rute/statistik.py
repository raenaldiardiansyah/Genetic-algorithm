"""Uji statistik untuk ringkasan hasil (dipakai scripts/06_ringkasan.py)."""
import numpy as np
from scipy.stats import rankdata


def holm(p):
    """Koreksi Holm untuk banyak p-value (step-down, hasil dibatasi maksimal 1)."""
    p = np.asarray(p, dtype=float)
    urut = np.argsort(p)
    m = len(p)
    hasil = np.empty(m)
    maks = 0.0
    for rank, i in enumerate(urut):
        maks = max(maks, (m - rank) * p[i])
        hasil[i] = min(1.0, maks)
    return hasil


def efek_rank_biserial(d):
    """Efek rank-biserial berpasangan: +1 bila semua selisih positif, -1 bila semua negatif."""
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    r = rankdata(np.abs(d))
    plus, minus = r[d > 0].sum(), r[d < 0].sum()
    return (plus - minus) / (plus + minus)
