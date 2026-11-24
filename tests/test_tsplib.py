import numpy as np
from ga_rute.tsplib import baca_tsplib
from ga_rute.ga import jalankan_ga
from ga_rute.baselines import held_karp


def test_baca_euc2d_dan_atsp(tmp_path):
    rng = np.random.default_rng(3)
    xy = rng.uniform(0, 100, size=(9, 2))
    isi = ("NAME : uji\nTYPE : TSP\nDIMENSION : 9\nEDGE_WEIGHT_TYPE : EUC_2D\nNODE_COORD_SECTION\n"
           + "\n".join(f"{i+1} {x:.4f} {y:.4f}" for i, (x, y) in enumerate(xy)) + "\nEOF\n")
    p = tmp_path / "uji.tsp"
    p.write_text(isi)
    D = baca_tsplib(p)
    assert D.shape == (9, 9) and np.allclose(D, D.T) and np.all(np.diag(D) == 0)
    jarak01 = np.floor(np.hypot(*(xy[0] - xy[1])) + 0.5)
    assert D[0, 1] == jarak01

    M = rng.integers(5, 90, size=(8, 8))
    isi = ("NAME : ujiatsp\nTYPE : ATSP\nDIMENSION : 8\nEDGE_WEIGHT_TYPE : EXPLICIT\n"
           "EDGE_WEIGHT_FORMAT : FULL_MATRIX\nEDGE_WEIGHT_SECTION\n"
           + "\n".join(" ".join(str(int(v)) for v in baris) for baris in M) + "\nEOF\n")
    q = tmp_path / "uji.atsp"
    q.write_text(isi)
    A = baca_tsplib(q)
    assert A.shape == (8, 8) and A[2, 5] == M[2, 5] and A[5, 2] == M[5, 2]
    _, opt = held_karp(A)
    _, ga, _ = jalankan_ga(A, 60, 200, seed=1)
    assert ga >= opt - 1e-9 and ga <= opt * 1.05
