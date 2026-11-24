import itertools
import numpy as np
from ga_rute.ga import (panjang_rute, panjang_populasi, order_crossover,
                        mutasi_inversi, jalankan_ga, order_crossover_batch,
                        mutasi_inversi_batch)
from ga_rute.baselines import nearest_neighbor, held_karp


def matriks_acak(n_toko, seed=1):
    rng = np.random.default_rng(seed)
    D = rng.uniform(1, 10, size=(n_toko + 1, n_toko + 1))  # asimetris
    np.fill_diagonal(D, 0)
    return D


def brute_force(D):
    n = D.shape[0] - 1
    return min(panjang_rute(D, np.array(p)) for p in itertools.permutations(range(1, n + 1)))


def test_contoh_slide_ox():
    # Contoh di slide: segmen 3 4 5 dari induk 1, sisanya dari induk 2 mulai setelah segmen
    class RngTetap:
        def choice(self, n, size, replace):
            return np.array([2, 5])

    p1 = np.array([1, 2, 3, 4, 5, 6, 7])
    p2 = np.array([5, 7, 6, 1, 3, 2, 4])
    anak = order_crossover(p1, p2, RngTetap())
    assert anak.tolist() == [6, 1, 3, 4, 5, 2, 7]


def test_ox_dan_inversi_menghasilkan_permutasi_valid():
    rng = np.random.default_rng(0)
    for _ in range(200):
        p1, p2 = rng.permutation(12) + 1, rng.permutation(12) + 1
        anak = order_crossover(p1, p2, rng)
        assert sorted(anak.tolist()) == list(range(1, 13))
        mut = mutasi_inversi(anak, rng)
        assert sorted(mut.tolist()) == list(range(1, 13))


def test_panjang_populasi_sama_dengan_satu_per_satu():
    D = matriks_acak(6)
    rng = np.random.default_rng(3)
    pop = np.array([rng.permutation(6) + 1 for _ in range(5)])
    assert np.allclose(panjang_populasi(D, pop), [panjang_rute(D, r) for r in pop])


def test_held_karp_sama_dengan_brute_force():
    D = matriks_acak(7)
    rute, total = held_karp(D)
    assert np.isclose(total, brute_force(D))
    assert np.isclose(panjang_rute(D, rute), total)


def test_nn_tidak_lebih_baik_dari_optimal():
    D = matriks_acak(8)
    _, opt = held_karp(D)
    _, nn = nearest_neighbor(D)
    assert nn >= opt - 1e-9


def test_ga_menemukan_optimal_pada_kasus_kecil():
    D = matriks_acak(8)
    _, opt = held_karp(D)
    _, hasil, riwayat = jalankan_ga(D, ukuran_pop=60, generasi=200, seed=5)
    assert hasil <= opt * 1.001
    assert riwayat[-1] <= riwayat[0]  # elitisme: tidak pernah memburuk


def test_diversitas_dijaga_agar_tidak_macet():
    # Tanpa penjaga keragaman populasi kolaps jadi 1 individu; dengan penjaga GA lebih baik
    hasil_jaga, hasil_tanpa = [], []
    for s in range(5):
        D = matriks_acak(10, seed=s)
        _, opt = held_karp(D)
        hasil_jaga.append(jalankan_ga(D, 100, 300, seed=s, jaga_keragaman=True)[1] / opt)
        hasil_tanpa.append(jalankan_ga(D, 100, 300, seed=s, jaga_keragaman=False)[1] / opt)
    assert np.mean(hasil_jaga) < np.mean(hasil_tanpa)


def test_ox_batch_sama_dengan_ox_satuan():
    rng = np.random.default_rng(11)
    n, B = 9, 60
    p1 = np.array([rng.permutation(n) + 1 for _ in range(B)])
    p2 = np.array([rng.permutation(n) + 1 for _ in range(B)])
    a = np.zeros(B, dtype=int); b = np.zeros(B, dtype=int)
    for i in range(B):
        a[i], b[i] = sorted(rng.choice(n + 1, size=2, replace=False))
    batch = order_crossover_batch(p1, p2, a, b)

    class RngTetap:
        def __init__(self, a, b): self.ab = np.array([a, b])
        def choice(self, n, size, replace): return self.ab

    for i in range(B):
        satuan = order_crossover(p1[i], p2[i], RngTetap(a[i], b[i]))
        assert batch[i].tolist() == satuan.tolist()
        assert sorted(batch[i].tolist()) == list(range(1, n + 1))


def test_inversi_batch_membalik_potongan():
    pop = np.array([[3, 1, 4, 2, 5], [1, 2, 3, 4, 5]])
    hasil = mutasi_inversi_batch(pop, np.array([1, 0]), np.array([4, 5]))
    assert hasil.tolist() == [[3, 2, 4, 1, 5], [5, 4, 3, 2, 1]]
