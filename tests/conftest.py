"""Configuración común de pytest: datos de ejemplo y utilidades."""

import os
import sys

import numpy as np
import pytest

# Permite importar ``app`` y ``solver`` desde la raíz del proyecto.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ejemplo SunRay Transport (Taha, cap. 5).
SUNRAY = {
    "costos": [[10, 2, 20, 11], [12, 7, 9, 20], [4, 14, 16, 18]],
    "oferta": [15, 25, 10],
    "demanda": [5, 15, 15, 15],
}

# Ejemplo de asignación (Taha, cap. 5).
ASIGNACION_TAHA = [[15, 10, 9], [9, 15, 10], [10, 12, 8]]


@pytest.fixture
def sunray():
    return {k: [list(f) if isinstance(f, list) else f for f in v]
            for k, v in SUNRAY.items()}


def es_factible(X, oferta, demanda, tol=1e-6):
    """Comprueba que X respeta oferta, demanda y no negatividad."""
    X = np.asarray(X, dtype=float)
    return (np.all(X >= -tol)
            and np.allclose(X.sum(axis=1), oferta, atol=tol)
            and np.allclose(X.sum(axis=0), demanda, atol=tol))


def es_arbol(basicas, m, n):
    """Comprueba que las celdas básicas forman un árbol de expansión."""
    if len(basicas) != m + n - 1:
        return False
    padre = list(range(m + n))

    def buscar(x):
        while padre[x] != x:
            x = padre[x]
        return x

    for i, j in basicas:
        a, b = buscar(i), buscar(m + j)
        if a == b:
            return False  # ciclo
        padre[a] = b
    return True
