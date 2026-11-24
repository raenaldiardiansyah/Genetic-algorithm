import numpy as np
import pytest
from ga_rute.ga import (pmx, probabilitas_rank, perbaiki_2opt, panjang_rute,
                        jalankan_ga)
from ga_rute.baselines import held_karp


def matriks_acak(n_toko, seed=1):
    rng = np.random.default_rng(seed)
    D = rng.uniform(1, 10, size=(n_toko + 1, n_toko + 1))
    np.fill_diagonal(D, 0)
    return D


def test_pmx_menghasilkan_permutasi_valid_dan_mewarisi_segmen():
    rng = np.random.default_rng(0)
    for _ in range(300):
        p1, p2 = rng.permutation(12) + 1, rng.permutation(12) + 1

        class Tetap:
            def choice(self, n, size, replace):
                return np.array([3, 8])
        anak = pmx(p1, p2, Tetap())
        assert sorted(anak.tolist()) == list(range(1, 13))
        assert anak[3:8].tolist() == p1[3:8].tolist()
        anak2 = pmx(p1, p2, rng)
        assert sorted(anak2.tolist()) == list(range(1, 13))


def test_pmx_contoh_klasik():
    p1 = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    p2 = np.array([9, 3, 7, 8, 2, 6, 5, 1, 4])

    class Tetap:
        def choice(self, n, size, replace):
            return np.array([3, 6])
    assert pmx(p1, p2, Tetap()).tolist() == [9, 3, 7, 4, 5, 6, 2, 1, 8]


def test_probabilitas_rank_terbaik_paling_besar():
    p = probabilitas_rank(np.array([5.0, 1.0, 3.0, 9.0]))
    assert np.isclose(p.sum(), 1.0)
    assert np.argmax(p) == 1 and np.argmin(p) == 3


def test_2opt_tidak_memperburuk_dan_lokal_optimal():
    D = matriks_acak(12, seed=4)
    rng = np.random.default_rng(1)
    for _ in range(20):
        rute = rng.permutation(12) + 1
        baru = perbaiki_2opt(D, rute)
        assert sorted(baru.tolist()) == list(range(1, 13))
        assert panjang_rute(D, baru) <= panjang_rute(D, rute) + 1e-9
        # tidak ada pembalikan potongan yang masih memperbaiki
        for i in range(12):
            for j in range(i + 1, 12):
                c = baru.copy()
                c[i:j + 1] = c[i:j + 1][::-1]
                assert panjang_rute(D, c) >= panjang_rute(D, baru) - 1e-9


def test_opsi_ga_semuanya_jalan():
    D = matriks_acak(9, seed=2)
    _, opt = held_karp(D)
    for kw in (dict(crossover="pmx"), dict(seleksi="rank"),
               dict(lokal="akhir"), dict(lokal="elit")):
        rute, hasil, riwayat = jalankan_ga(D, 40, 60, seed=3, **kw)
        assert sorted(rute.tolist()) == list(range(1, 10))
        assert np.isclose(hasil, panjang_rute(D, rute))
        assert hasil >= opt - 1e-9


def test_ortools_tidak_lebih_buruk_dari_nn_dan_dekat_optimal():
    pytest.importorskip("ortools")
    from ga_rute.baselines import ortools_atsp, nearest_neighbor
    D = matriks_acak(9, seed=6)
    _, opt = held_karp(D)
    rute, km = ortools_atsp(D, detik=2)
    assert sorted(rute.tolist()) == list(range(1, 10))
    assert np.isclose(km, panjang_rute(D, rute))
    assert km <= nearest_neighbor(D)[1] + 1e-9
    assert km <= opt * 1.02


def test_callback_tidak_mengubah_hasil_dan_mencatat_per_generasi():
    D = matriks_acak(10, seed=8)
    catatan = []
    a = jalankan_ga(D, 50, 40, seed=2)
    b = jalankan_ga(D, 50, 40, seed=2, callback=lambda g, r, km: catatan.append((g, km)))
    assert a[0].tolist() == b[0].tolist() and a[1] == b[1]
    assert [g for g, _ in catatan] == list(range(40))
    km = [k for _, k in catatan]
    assert all(km[i + 1] <= km[i] + 1e-9 for i in range(len(km) - 1))   # elitisme: tidak memburuk
