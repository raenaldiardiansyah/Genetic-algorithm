"""Algoritma Genetika untuk ATSP satu truk.

Konvensi:
- D adalah matriks jarak (N+1) x (N+1). Indeks 0 = gudang, 1..N = toko.
- Kromosom = permutasi toko 1..N (gudang tidak dikodekan).
- Panjang rute = D[0,t1] + sum D[tk,tk+1] + D[tN,0]  (boleh asimetris).
"""
import numpy as np


def panjang_rute(D, rute):
    """Panjang satu rute (array berisi indeks toko)."""
    total = D[0, rute[0]] + D[rute[-1], 0]
    total += D[rute[:-1], rute[1:]].sum()
    return total


def panjang_populasi(D, pop):
    """Panjang semua rute sekaligus. pop berukuran (P, N)."""
    awal = D[0, pop[:, 0]]
    akhir = D[pop[:, -1], 0]
    tengah = D[pop[:, :-1], pop[:, 1:]].sum(axis=1)
    return awal + tengah + akhir


def populasi_acak(n_toko, ukuran, rng):
    return np.array([rng.permutation(n_toko) + 1 for _ in range(ukuran)])


def seleksi_turnamen(panjang, rng, k=3):
    """Ambil k individu acak, kembalikan indeks yang rutenya terpendek."""
    kandidat = rng.integers(0, len(panjang), size=k)
    return kandidat[np.argmin(panjang[kandidat])]


def order_crossover(p1, p2, rng):
    """OX: segmen tengah dari induk 1, sisanya urutan induk 2 mulai setelah segmen."""
    n = len(p1)
    a, b = sorted(rng.choice(n + 1, size=2, replace=False))
    anak = np.zeros(n, dtype=p1.dtype)
    anak[a:b] = p1[a:b]
    dipakai = set(p1[a:b].tolist())
    # urutan induk 2 dimulai dari posisi b (melingkar)
    urutan = np.concatenate([p2[b:], p2[:b]])
    sisa = [g for g in urutan if g not in dipakai]
    posisi = list(range(b, n)) + list(range(0, a))
    for pos, gen in zip(posisi, sisa):
        anak[pos] = gen
    return anak


def mutasi_inversi(rute, rng):
    """Balik satu potongan rute."""
    n = len(rute)
    a, b = sorted(rng.choice(n + 1, size=2, replace=False))
    hasil = rute.copy()
    hasil[a:b] = hasil[a:b][::-1]
    return hasil


def order_crossover_batch(p1, p2, a, b):
    """OX untuk banyak pasangan induk sekaligus (tanpa loop Python).

    p1, p2: (B, N) permutasi toko 1..N. a, b: (B,) batas segmen [a, b) dari induk 1.
    Hasilnya sama persis dengan order_crossover untuk batas yang sama.
    """
    B, n = p1.shape
    pos = np.arange(n)[None, :]
    segmask = (pos >= a[:, None]) & (pos < b[:, None])
    idx = (pos + b[:, None]) % n                      # urutan induk 2 mulai setelah segmen
    p2r = np.take_along_axis(p2, idx, axis=1)
    ada = np.zeros((B, n + 1), dtype=bool)            # gen yang sudah ada di segmen
    r, c = np.nonzero(segmask)
    ada[r, p1[r, c]] = True
    sisa = ~np.take_along_axis(ada, p2r, axis=1)
    segr = np.take_along_axis(segmask, idx, axis=1)
    anak = np.zeros_like(p1)
    anak[segmask] = p1[segmask]
    rr, cc = np.nonzero(~segr)
    anak[rr, idx[rr, cc]] = p2r[sisa]
    return anak


def mutasi_inversi_batch(pop, a, b):
    """Balik potongan [a, b) pada setiap baris."""
    n = pop.shape[1]
    pos = np.arange(n)[None, :]
    dalam = (pos >= a[:, None]) & (pos < b[:, None])
    idx = np.where(dalam, a[:, None] + b[:, None] - 1 - pos, pos)
    return np.take_along_axis(pop, idx, axis=1)


def _dua_batas(rng, banyak, n):
    """Pasangan batas a < b di 0..n, seragam atas semua pasangan berbeda."""
    x = rng.integers(0, n + 1, size=banyak)
    y = rng.integers(0, n, size=banyak)
    y = y + (y >= x)
    return np.minimum(x, y), np.maximum(x, y)


def pmx(p1, p2, rng):
    """Partially Mapped Crossover: segmen dari induk 1, sisanya dipetakan dari induk 2."""
    n = len(p1)
    a, b = sorted(rng.choice(n + 1, size=2, replace=False))
    anak = p2.copy()
    anak[a:b] = p1[a:b]
    peta = {int(p1[i]): int(p2[i]) for i in range(a, b)}
    segmen = set(peta)
    for i in list(range(0, a)) + list(range(b, n)):
        g = int(p2[i])
        while g in segmen:
            g = peta[g]
        anak[i] = g
    return anak


def probabilitas_rank(panjang, tekanan=1.5):
    """Seleksi berbasis peringkat (linear ranking): rute terpendek peluangnya paling besar."""
    P = len(panjang)
    rank = np.empty(P, dtype=int)
    rank[np.argsort(panjang)[::-1]] = np.arange(P)      # terburuk = 0, terbaik = P-1
    prob = (2 - tekanan + 2 * (tekanan - 1) * rank / (P - 1)) / P
    return prob / prob.sum()


def perbaiki_2opt(D, rute, maks_iter=200):
    """2-opt untuk ATSP: balik potongan rute selama jarak total mengecil.

    Pada jarak asimetris, membalik potongan mengubah biaya di dalam potongan, jadi
    dipakai jumlah kumulatif arah maju dan arah mundur (O(n^2) per putaran).
    """
    n = len(rute)
    r = np.concatenate([[0], rute, [0]]).astype(int)
    I = np.arange(1, n + 1)[:, None]
    J = np.arange(1, n + 1)[None, :]
    mask = I < J
    for _ in range(maks_iter):
        F = np.concatenate([[0.0], np.cumsum(D[r[:-1], r[1:]])])    # arah maju
        Bk = np.concatenate([[0.0], np.cumsum(D[r[1:], r[:-1]])])   # arah mundur
        lama = D[r[I - 1], r[I]] + (F[J] - F[I]) + D[r[J], r[J + 1]]
        baru = D[r[I - 1], r[J]] + (Bk[J] - Bk[I]) + D[r[I], r[J + 1]]
        delta = np.where(mask, baru - lama, 0.0)
        k = int(np.argmin(delta))
        i, j = divmod(k, n)
        if delta[i, j] > -1e-9:
            break
        r[i + 1:j + 2] = r[i + 1:j + 2][::-1].copy()
    return r[1:-1]


def jalankan_ga(D, ukuran_pop=100, generasi=1000, p_cx=0.9, p_mut=0.2,
                k_turnamen=3, n_elit=2, seed=0, jaga_keragaman=True,
                crossover="ox", seleksi="turnamen", lokal=None, callback=None):
    """Jalankan GA. Kembalikan (rute_terbaik, panjang_terbaik, riwayat).

    Seluruh generasi baru dibuat sekaligus dengan operasi numpy (cepat).
    jaga_keragaman: anak kembar dari individu yang sudah ada dimutasi sampai unik.
    crossover: "ox" (cepat, batch) atau "pmx".  seleksi: "turnamen" atau "rank".
    lokal: None (GA murni), "elit" (2-opt pada individu terbaik tiap generasi),
           "akhir" (2-opt hanya pada hasil akhir).
    callback: fungsi opsional callback(generasi, rute_terbaik, panjang) dipanggil tiap generasi
              (dipakai untuk visualisasi; tidak mengubah hasil).
    """
    rng = np.random.default_rng(seed)
    n = D.shape[0] - 1
    pop = populasi_acak(n, ukuran_pop, rng)
    n_anak = ukuran_pop - n_elit
    riwayat = []

    for gen in range(generasi):
        panjang = panjang_populasi(D, pop)
        urut = np.argsort(panjang)
        if lokal == "elit":                      # 2-opt pada individu terbaik
            pop[urut[0]] = perbaiki_2opt(D, pop[urut[0]])
            panjang[urut[0]] = panjang_rute(D, pop[urut[0]])
        riwayat.append(panjang[urut[0]])
        if callback is not None:
            callback(gen, pop[urut[0]].copy(), float(panjang[urut[0]]))
        elit = pop[urut[:n_elit]]

        # seleksi induk untuk semua anak sekaligus
        if seleksi == "rank":
            menang = rng.choice(ukuran_pop, size=2 * n_anak, p=probabilitas_rank(panjang))
        else:
            kand = rng.integers(0, ukuran_pop, size=(2 * n_anak, k_turnamen))
            menang = kand[np.arange(2 * n_anak), np.argmin(panjang[kand], axis=1)]
        p1, p2 = pop[menang[:n_anak]], pop[menang[n_anak:]]

        # crossover OX (sebagian pasangan tidak di-crossover: anak = induk 1)
        if crossover == "pmx":
            anak = np.array([pmx(p1[i], p2[i], rng) for i in range(n_anak)])
        else:
            a, b = _dua_batas(rng, n_anak, n)
            anak = order_crossover_batch(p1, p2, a, b)
        anak = np.where((rng.random(n_anak) < p_cx)[:, None], anak, p1)

        # mutasi inversi
        a, b = _dua_batas(rng, n_anak, n)
        anak = np.where((rng.random(n_anak) < p_mut)[:, None],
                        mutasi_inversi_batch(anak, a, b), anak)

        if jaga_keragaman:
            sudah_ada = {r.tobytes() for r in elit}
            for i in range(n_anak):
                baris = anak[i]
                for _ in range(10):
                    if baris.tobytes() not in sudah_ada:
                        break
                    baris = mutasi_inversi(baris, rng)
                sudah_ada.add(baris.tobytes())
                anak[i] = baris
        pop = np.vstack([elit, anak])

    panjang = panjang_populasi(D, pop)
    i = int(np.argmin(panjang))
    terbaik = pop[i]
    akhir = float(panjang[i])
    if lokal in ("elit", "akhir"):
        terbaik = perbaiki_2opt(D, terbaik)
        akhir = float(panjang_rute(D, terbaik))
    riwayat.append(akhir)
    return terbaik, akhir, np.array(riwayat)
