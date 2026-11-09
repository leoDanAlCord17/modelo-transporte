"""Pruebas de balanceo y de los métodos de solución inicial."""

import numpy as np
import pytest

from conftest import SUNRAY, es_arbol, es_factible
from solver.balance import balancear
from solver.iniciales import METODOS, costo_minimo, esquina_noroeste, vogel


# --- Valores del libro de Taha ---------------------------------------------
@pytest.mark.parametrize("metodo, esperado", [
    (esquina_noroeste, 520),
    (costo_minimo, 475),
    (vogel, 475),
])
def test_sunray_costos_iniciales_taha(metodo, esperado):
    r = metodo(SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"])
    assert r["costo_total"] == pytest.approx(esperado)


def test_noroeste_asignacion_taha():
    r = esquina_noroeste(SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"])
    esperado = [[5, 10, 0, 0], [0, 5, 15, 5], [0, 0, 0, 10]]
    assert np.allclose(r["asignacion"], esperado)


@pytest.mark.parametrize("nombre", list(METODOS))
def test_todas_factibles_y_arbol(nombre):
    r = METODOS[nombre](SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"])
    assert es_factible(r["asignacion"], SUNRAY["oferta"], SUNRAY["demanda"])
    assert es_arbol(r["basicas"], 3, 4)
    assert len(r["pasos"]) == 3 + 4 - 1


def test_vogel_guarda_penalizaciones():
    r = vogel(SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"])
    p1 = r["pasos"][0]
    # Penalizaciones del primer paso (Taha): filas 8, 2, 10; columnas 6, 5, 7, 7
    assert p1["penalizaciones_filas"] == [8, 2, 10]
    assert p1["penalizaciones_columnas"] == [6, 5, 7, 7]
    assert p1["linea_elegida"] == {"tipo": "fila", "indice": 2, "penalizacion": 10}
    assert p1["celda"] == [2, 0]


def test_costo_minimo_desempate_mayor_cantidad():
    # Dos celdas con costo 1: (0,0) puede recibir 2 y (1,1) puede recibir 8.
    C = [[1, 5], [5, 1]]
    r = costo_minimo(C, [2, 8], [2, 8])
    assert r["pasos"][0]["celda"] == [1, 1]


# --- Degeneración -------------------------------------------------------------
def test_noroeste_degenerado_mantiene_m_mas_n_menos_1():
    # La fila 1 y la columna 1 se agotan a la vez (10 = 10).
    C = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    oferta, demanda = [10, 20, 30], [10, 20, 30]
    r = esquina_noroeste(C, oferta, demanda)
    assert len(r["basicas"]) == 5
    assert es_arbol(r["basicas"], 3, 3)
    assert any(p["degenerado"] for p in r["pasos"])
    assert es_factible(r["asignacion"], oferta, demanda)


@pytest.mark.parametrize("nombre", list(METODOS))
def test_degenerado_todos_los_metodos(nombre):
    C = [[4, 6, 8], [6, 8, 6], [5, 7, 6]]
    oferta, demanda = [5, 10, 15], [5, 10, 15]
    r = METODOS[nombre](C, oferta, demanda)
    assert es_arbol(r["basicas"], 3, 3)
    assert es_factible(r["asignacion"], oferta, demanda)


# --- Casos límite -------------------------------------------------------------
@pytest.mark.parametrize("nombre", list(METODOS))
def test_una_fila(nombre):
    r = METODOS[nombre]([[3, 1, 2]], [9], [2, 3, 4])
    assert np.allclose(r["asignacion"], [[2, 3, 4]])
    assert r["costo_total"] == pytest.approx(6 + 3 + 8)
    assert len(r["basicas"]) == 3


@pytest.mark.parametrize("nombre", list(METODOS))
def test_una_columna(nombre):
    r = METODOS[nombre]([[3], [1], [2]], [2, 3, 4], [9])
    assert np.allclose(r["asignacion"], [[2], [3], [4]])
    assert len(r["basicas"]) == 3


@pytest.mark.parametrize("nombre", list(METODOS))
def test_decimales(nombre):
    C = [[1.5, 2.25], [3.75, 0.5]]
    oferta, demanda = [10.5, 4.5], [7.25, 7.75]
    r = METODOS[nombre](C, oferta, demanda)
    assert es_factible(r["asignacion"], oferta, demanda)


# --- Balanceo -----------------------------------------------------------------
def test_balance_ya_balanceado():
    r = balancear(SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"])
    assert r["balanceado"] and r["ficticio"] is None
    assert r["costos"].shape == (3, 4)


def test_balance_oferta_mayor_agrega_destino():
    r = balancear([[1, 2], [3, 4]], [30, 20], [10, 15])
    assert r["ficticio"] == "destino"
    assert r["costos"].shape == (2, 3)
    assert r["demanda"][-1] == pytest.approx(25)
    assert np.all(r["costos"][:, -1] == 0)


def test_balance_demanda_mayor_agrega_origen():
    r = balancear([[1, 2], [3, 4]], [10, 5], [20, 15])
    assert r["ficticio"] == "origen"
    assert r["costos"].shape == (3, 2)
    assert r["oferta"][-1] == pytest.approx(20)
