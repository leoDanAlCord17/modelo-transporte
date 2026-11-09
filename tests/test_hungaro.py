"""Pruebas del método húngaro (modelo de asignación)."""

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment

from conftest import ASIGNACION_TAHA
from solver.hungaro import metodo_hungaro


def _optimo_scipy(C, maximizar=False):
    C = np.asarray(C, dtype=float)
    f, c = linear_sum_assignment(C, maximize=maximizar)
    return float(C[f, c].sum())


def test_ejemplo_taha():
    r = metodo_hungaro(ASIGNACION_TAHA)
    assert r["costo_total"] == 27
    assert r["asignacion"] == [[0, 1], [1, 0], [2, 2]]


def test_pasos_incluyen_reducciones():
    r = metodo_hungaro(ASIGNACION_TAHA)
    tipos = [p["tipo"] for p in r["pasos"]]
    assert tipos[0] == "reduccion_filas"
    assert tipos[1] == "reduccion_columnas"
    assert tipos[-1] == "asignacion"
    assert r["pasos"][0]["minimos"] == [9, 9, 8]
    assert r["pasos"][1]["minimos"] == [0, 1, 0]


def test_requiere_ajuste():
    # Ejemplo clásico donde tras las reducciones no bastan n líneas.
    C = [[9, 11, 14, 11, 7], [6, 15, 13, 13, 10], [12, 13, 6, 8, 8],
         [11, 9, 10, 12, 9], [7, 12, 14, 10, 14]]
    r = metodo_hungaro(C)
    assert any(p["tipo"] == "ajuste" for p in r["pasos"])
    assert r["costo_total"] == pytest.approx(_optimo_scipy(C))


def test_cada_fila_y_columna_una_vez():
    C = [[4, 1, 3], [2, 0, 5], [3, 2, 2]]
    r = metodo_hungaro(C)
    filas = [i for i, _ in r["asignacion"]]
    cols = [j for _, j in r["asignacion"]]
    assert sorted(filas) == [0, 1, 2] and sorted(cols) == [0, 1, 2]


def test_maximizacion():
    C = [[7, 5, 9], [3, 8, 6], [4, 2, 7]]
    r = metodo_hungaro(C, "max")
    assert r["costo_total"] == pytest.approx(_optimo_scipy(C, True))
    assert r["pasos"][0]["tipo"] == "conversion"


def test_no_cuadrada_mas_filas():
    C = [[5, 8], [3, 7], [6, 2], [4, 4]]
    r = metodo_hungaro(C)
    assert len(r["asignacion"]) == 2          # solo 2 tareas reales
    assert r["costo_total"] == pytest.approx(_optimo_scipy(C))
    assert any(p["tipo"] == "ficticios" for p in r["pasos"])


def test_no_cuadrada_mas_columnas():
    C = [[5, 8, 1, 9], [3, 7, 4, 2]]
    r = metodo_hungaro(C)
    assert len(r["asignacion"]) == 2
    assert r["costo_total"] == pytest.approx(_optimo_scipy(C))


def test_1x1():
    r = metodo_hungaro([[4]])
    assert r["asignacion"] == [[0, 0]] and r["costo_total"] == 4


def test_decimales():
    C = [[1.5, 2.75, 3.1], [0.25, 4.5, 2.2], [3.3, 1.1, 0.9]]
    r = metodo_hungaro(C)
    assert r["costo_total"] == pytest.approx(_optimo_scipy(C))


def test_aleatorio_contra_scipy():
    rng = np.random.default_rng(7)
    for _ in range(60):
        n, m = int(rng.integers(1, 9)), int(rng.integers(1, 9))
        C = rng.integers(0, 40, size=(n, m)).astype(float)
        maximizar = bool(rng.random() < 0.3)
        r = metodo_hungaro(C.tolist(), "max" if maximizar else "min")
        assert r["costo_total"] == pytest.approx(_optimo_scipy(C, maximizar)), C
