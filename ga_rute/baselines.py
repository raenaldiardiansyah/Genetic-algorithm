"""Pembanding: Nearest Neighbor dan Held-Karp (optimal, hanya untuk N kecil)."""
import numpy as np


def nearest_neighbor(D):
    """Selalu ke toko terdekat yang belum dikunjungi. Kembalikan (rute, panjang)."""
    n = D.shape[0] - 1
    belum = set(range(1, n + 1))
    posisi, rute, total = 0, [], 0.0
    while belum:
        tujuan = min(belum, key=lambda j: D[posisi, j])
        total += D[posisi, tujuan]
        rute.append(tujuan)
        belum.remove(tujuan)
        posisi = tujuan
    total += D[posisi, 0]
    return np.array(rute), float(total)


def held_karp(D):
    """Rute optimal ATSP dengan dynamic programming. Praktis untuk N <= 15."""
    n = D.shape[0] - 1
    penuh = 1 << n
    dp = np.full((penuh, n), np.inf)
    induk = np.full((penuh, n), -1, dtype=int)
    for j in range(n):
        dp[1 << j, j] = D[0, j + 1]
    for mask in range(1, penuh):
        for j in range(n):
            if not (mask >> j) & 1 or mask == (1 << j):
                continue
            prev = mask ^ (1 << j)
            kandidat = dp[prev, :] + D[1:n + 1, j + 1]
            k = int(np.argmin(kandidat))
            dp[mask, j] = kandidat[k]
            induk[mask, j] = k
    akhir = dp[penuh - 1, :] + D[1:n + 1, 0]
    j = int(np.argmin(akhir))
    total = float(akhir[j])
    rute, mask = [], penuh - 1
    while j != -1:
        rute.append(j + 1)
        k = induk[mask, j]
        mask ^= (1 << j)
        j = k
    return np.array(rute[::-1]), total


def ortools_atsp(D, detik=5, skala=1000):
    """Patokan OR-Tools (guided local search). Kembalikan (rute toko 1..N, panjang km).

    Jarak dibulatkan ke 1/skala km (skala 1000 = meter) karena OR-Tools memakai bilangan bulat.
    Hasil 'best-known' bergantung pada batas waktu `detik`.
    """
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    n = D.shape[0]
    bulat = np.rint(D * skala).astype(np.int64)
    manajer = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manajer)

    def biaya(i, j):
        return int(bulat[manajer.IndexToNode(i), manajer.IndexToNode(j)])

    routing.SetArcCostEvaluatorOfAllVehicles(routing.RegisterTransitCallback(biaya))
    p = pywrapcp.DefaultRoutingSearchParameters()
    p.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    p.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    p.time_limit.seconds = int(detik)
    solusi = routing.SolveWithParameters(p)
    if solusi is None:
        raise RuntimeError("OR-Tools tidak menemukan solusi")
    idx, rute = routing.Start(0), []
    while not routing.IsEnd(idx):
        simpul = manajer.IndexToNode(idx)
        if simpul != 0:
            rute.append(simpul)
        idx = solusi.Value(routing.NextVar(idx))
    rute = np.array(rute)
    total = D[0, rute[0]] + D[rute[:-1], rute[1:]].sum() + D[rute[-1], 0]
    return rute, float(total)
