"""Pruebas del método MODI y de la orquestación del transporte."""

import numpy as np
import pytest

from conftest import SUNRAY, es_arbol, es_factible
from solver.iniciales import METODOS, esquina_noroeste
from solver.optimo import encontrar_ciclo, modi
from solver.transporte import comparar_metodos, resolver_transporte
from solver.verificacion import linprog_transporte

# Óptimo del ejemplo SunRay verificado con scipy.optimize.linprog.
OPTIMO_SUNRAY = 435


@pytest.mark.parametrize("metodo", ["noroeste", "costo_minimo", "vogel"])
def test_sunray_optimo(metodo):
    r = resolver_transporte(SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"], metodo)
    assert r["optimo"]["costo_total"] == pytest.approx(OPTIMO_SUNRAY)
    assert r["verificacion_scipy"]["coincide"] is True
    assert r["verificacion_scipy"]["costo_total"] == pytest.approx(OPTIMO_SUNRAY)


def test_sunray_linprog_confirma_435():
    assert linprog_transporte(**SUNRAY) == pytest.approx(OPTIMO_SUNRAY)


def test_sunray_primera_iteracion_noroeste():
    """Primera iteración MODI desde la Esquina NO (Taha, ejemplo 5.3-5)."""
    r = resolver_transporte(SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"], "noroeste")
    it = r["optimo"]["iteraciones"][0]
    assert it["u"] == [0, 5, 3]
    assert it["v"] == [10, 2, 4, 15]
    assert it["celda_entrante"] == [2, 0]          # x31 entra
    assert it["theta"] == 5
    # costo reducido d31 = 4 − 3 − 10 = −9 → nuevo costo = 520 − 9·5 = 475
    assert it["costos_reducidos"][2][0] == -9
    assert it["costo"] == pytest.approx(475)
    assert it["signos"][0] == "+"
    assert len(it["ciclo"]) % 2 == 0


def test_ultima_iteracion_es_optima():
    r = resolver_transporte(SUNRAY["costos"], SUNRAY["oferta"], SUNRAY["demanda"], "vogel")
    ultima = r["optimo"]["iteraciones"][-1]
    assert ultima["optima"] is True
    assert ultima["celda_entrante"] is None
    assert min(min(f) for f in ultima["costos_reducidos"]) >= 0


def test_ciclo_es_cerrado_y_alterna():
    ini = esquina_noroeste(**SUNRAY)
    ciclo = encontrar_ciclo(ini["basicas"], (2, 0), 3, 4)
    assert ciclo[0] == (2, 0)
    for k in range(len(ciclo)):
        a, b = ciclo[k], ciclo[(k + 1) % len(ciclo)]
        # celdas consecutivas comparten fila o columna (alternadamente)
        assert a[0] == b[0] or a[1] == b[1]
    assert set(ciclo[1:]) <= set(ini["basicas"])


def test_modi_mantiene_arbol_en_cada_iteracion():
    ini = esquina_noroeste(**SUNRAY)
    r = modi(SUNRAY["costos"], ini["asignacion"], ini["basicas"])
    for it in r["iteraciones"]:
        assert es_arbol([tuple(c) for c in it["basicas"]], 3, 4)
    assert es_factible(r["asignacion"], SUNRAY["oferta"], SUNRAY["demanda"])


# --- No balanceados ---------------------------------------------------------
def test_oferta_mayor_que_demanda():
    C = [[4, 8, 8], [16, 24, 16], [8, 16, 24]]
    r = resolver_transporte(C, [76, 82, 77], [72, 102, 41], "vogel")
    assert r["balanceado"] is False and r["ficticio"] == "destino"
    assert r["nombres_destinos"][-1] == "Ficticio"
    assert r["verificacion_scipy"]["coincide"]
    # Lo enviado al destino ficticio es la oferta no utilizada (235 − 215 = 20)
    ficticios = [e for e in r["optimo"]["envios"] if e["ficticio"]]
    assert sum(e["cantidad"] for e in ficticios) == pytest.approx(20)


def test_demanda_mayor_que_oferta():
    C = [[5, 3, 6], [4, 7, 2]]
    r = resolver_transporte(C, [30, 20], [25, 25, 20], "costo_minimo")
    assert r["ficticio"] == "origen"
    assert len(r["costos"]) == 3
    assert r["verificacion_scipy"]["coincide"]


# --- Degenerado ---------------------------------------------------------------
@pytest.mark.parametrize("metodo", ["noroeste", "costo_minimo", "vogel"])
def test_problema_degenerado(metodo):
    C = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    r = resolver_transporte(C, [10, 20, 30], [10, 20, 30], metodo)
    assert r["verificacion_scipy"]["coincide"]
    assert len(r["optimo"]["basicas"]) == 5


# --- 1×n y m×1 ---------------------------------------------------------------
def test_1xn():
    r = resolver_transporte([[3, 1, 2]], [9], [2, 3, 4])
    assert r["optimo"]["costo_total"] == 17
    assert r["optimo"]["numero_iteraciones"] == 0


def test_mx1():
    r = resolver_transporte([[3], [1], [2]], [2, 3, 4], [9])
    assert r["optimo"]["costo_total"] == 17


def test_1x1():
    r = resolver_transporte([[7]], [5], [5])
    assert r["optimo"]["costo_total"] == 35


# --- Maximización y decimales ------------------------------------------------
def test_maximizacion():
    B = [[10, 2, 20, 11], [12, 7, 9, 20], [4, 14, 16, 18]]
    r = resolver_transporte(B, SUNRAY["oferta"], SUNRAY["demanda"], "vogel", "max")
    esperado = -linprog_transporte(-np.array(B, float), SUNRAY["oferta"], SUNRAY["demanda"])
    assert r["optimo"]["costo_total"] == pytest.approx(esperado)
    assert r["verificacion_scipy"]["coincide"]
    assert r["optimo"]["costo_total"] >= r["inicial"]["costo_total"]


def test_maximizacion_no_balanceada():
    B = [[5, 9], [7, 3], [6, 6]]
    r = resolver_transporte(B, [10, 10, 10], [12, 8], "costo_minimo", "max")
    assert r["ficticio"] == "destino"
    assert r["verificacion_scipy"]["coincide"]


def test_decimales():
    C = [[1.5, 2.25, 3.1], [3.75, 0.5, 2.2]]
    r = resolver_transporte(C, [10.5, 4.5], [5.25, 6.75, 3.0], "vogel")
    assert r["verificacion_scipy"]["coincide"]
    assert es_factible(r["optimo"]["asignacion"], r["oferta"], r["demanda"])


# --- Comparación de métodos --------------------------------------------------
def test_comparar_metodos_sunray():
    r = comparar_metodos(**SUNRAY)
    por_metodo = {f["metodo"]: f for f in r["metodos"]}
    assert por_metodo["noroeste"]["costo_inicial"] == 520
    assert por_metodo["costo_minimo"]["costo_inicial"] == 475
    assert por_metodo["vogel"]["costo_inicial"] == 475
    assert all(f["costo_optimo"] == OPTIMO_SUNRAY for f in r["metodos"])


# --- Prueba aleatoria contra linprog ---------------------------------------
def _problema_aleatorio(rng):
    m, n = int(rng.integers(1, 7)), int(rng.integers(1, 7))
    C = rng.integers(0, 30, size=(m, n)).astype(float)
    oferta = rng.integers(1, 50, size=m).astype(float)
    demanda = rng.integers(1, 50, size=n).astype(float)
    if rng.random() < 0.5:  # la mitad de los casos balanceados a la fuerza
        dif = oferta.sum() - demanda.sum()
        if dif > 0:
            demanda[-1] += dif
        else:
            oferta[-1] -= dif
    return C.tolist(), oferta.tolist(), demanda.tolist()


@pytest.mark.parametrize("metodo", ["noroeste", "costo_minimo", "vogel"])
def test_aleatorio_50_problemas_contra_linprog(metodo):
    rng = np.random.default_rng(2024)
    for _ in range(50):
        C, a, b = _problema_aleatorio(rng)
        objetivo = "max" if rng.random() < 0.3 else "min"
        r = resolver_transporte(C, a, b, metodo, objetivo)
        assert r["verificacion_scipy"]["coincide"], (C, a, b, objetivo)
        assert es_factible(r["optimo"]["asignacion"], r["oferta"], r["demanda"])
        m, n = len(r["costos"]), len(r["costos"][0])
        assert es_arbol([tuple(c) for c in r["optimo"]["basicas"]], m, n)
