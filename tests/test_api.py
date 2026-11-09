"""Pruebas de las rutas Flask y de la API JSON."""

import pytest

from app import app
from conftest import ASIGNACION_TAHA, SUNRAY


@pytest.fixture
def cliente():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# --- Páginas -----------------------------------------------------------------
@pytest.mark.parametrize("ruta", ["/", "/transporte", "/asignacion", "/documentacion"])
def test_paginas_responden(cliente, ruta):
    r = cliente.get(ruta)
    assert r.status_code == 200
    assert "text/html" in r.content_type
    assert b"/css/styles.css" in r.data


def test_estaticos_locales(cliente):
    assert cliente.get("/css/styles.css").status_code == 200
    assert cliente.get("/js/transporte.js").status_code == 200
    assert cliente.get("/js/asignacion.js").status_code == 200


def test_en_vercel_no_se_registra_ruta_de_estaticos():
    """Con la variable VERCEL definida, Flask no sirve public/ (lo hace la CDN)."""
    import os
    import subprocess
    import sys
    codigo = ("import app; print(any(r.endpoint == 'estaticos_locales' "
              "for r in app.app.url_map.iter_rules()), app.app.static_folder)")
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=raiz, capture_output=True,
                            text=True, env={**os.environ, "VERCEL": "1"}, check=True)
    assert salida.stdout.split() == ["False", "None"]


def test_404_pagina(cliente):
    assert cliente.get("/no-existe").status_code == 404


# --- /api/transporte ---------------------------------------------------------
@pytest.mark.parametrize("metodo, inicial", [
    ("noroeste", 520), ("costo_minimo", 475), ("vogel", 475)])
def test_api_transporte_sunray(cliente, metodo, inicial):
    r = cliente.post("/api/transporte", json={**SUNRAY, "metodo_inicial": metodo})
    assert r.status_code == 200
    d = r.get_json()
    assert d["balanceado"] is True and d["ficticio"] is None
    assert d["inicial"]["costo_total"] == inicial
    assert d["optimo"]["costo_total"] == 435
    assert d["verificacion_scipy"]["coincide"] is True
    it = d["optimo"]["iteraciones"][0]
    for clave in ("u", "v", "costos_reducidos", "celda_entrante", "ciclo",
                  "theta", "asignacion_resultante", "costo"):
        assert clave in it


def test_api_transporte_nombres(cliente):
    datos = {**SUNRAY, "nombres_origenes": ["Los Ángeles", "Detroit", "Nueva Orleans"],
             "nombres_destinos": ["Denver", "Miami", "", "Dallas"]}
    d = cliente.post("/api/transporte", json=datos).get_json()
    assert d["nombres_origenes"][0] == "Los Ángeles"
    assert d["nombres_destinos"][2] == "D3"  # vacío → nombre por defecto
    assert any(e["origen"] == "Los Ángeles" for e in d["optimo"]["envios"])


def test_api_transporte_no_balanceado(cliente):
    datos = {"costos": [[1, 2], [3, 4]], "oferta": [30, 20], "demanda": [10, 15]}
    d = cliente.post("/api/transporte", json=datos).get_json()
    assert d["balanceado"] is False
    assert d["ficticio"] == "destino"
    assert d["cantidad_ficticia"] == 25


def test_api_transporte_max(cliente):
    d = cliente.post("/api/transporte",
                     json={**SUNRAY, "objetivo": "max"}).get_json()
    assert d["objetivo"] == "max"
    assert d["verificacion_scipy"]["coincide"]


def test_api_transporte_acepta_texto_numerico(cliente):
    datos = {"costos": [["1,5", "2"]], "oferta": ["3"], "demanda": [1, 2]}
    r = cliente.post("/api/transporte", json=datos)
    assert r.status_code == 200


def test_api_comparar(cliente):
    d = cliente.post("/api/comparar", json=SUNRAY).get_json()
    assert [f["costo_inicial"] for f in d["metodos"]] == [520, 475, 475]
    assert all(f["costo_optimo"] == 435 for f in d["metodos"])


# --- Entradas inválidas -> 400 ------------------------------------------------
@pytest.mark.parametrize("datos, fragmento", [
    ({}, "obligatoria"),
    ({"costos": [], "oferta": [], "demanda": []}, "obligatoria"),
    ({"costos": [[1, 2], [3]], "oferta": [1, 1], "demanda": [1, 1]}, "columnas"),
    ({"costos": [[1, -2]], "oferta": [3], "demanda": [1, 2]}, "negativos"),
    ({"costos": [[1, "abc"]], "oferta": [3], "demanda": [1, 2]}, "no es un número"),
    ({"costos": [[1, None]], "oferta": [3], "demanda": [1, 2]}, "vacío"),
    ({"costos": [[1, ""]], "oferta": [3], "demanda": [1, 2]}, "vacío"),
    ({"costos": [[1, True]], "oferta": [3], "demanda": [1, 2]}, "numérico"),
    ({"costos": [[1, 2]], "oferta": [3, 4], "demanda": [1, 2]}, "oferta"),
    ({"costos": [[1, 2]], "oferta": [3], "demanda": [1]}, "demanda"),
    ({"costos": [[1, 2]], "oferta": [0], "demanda": [1, 2]}, "mayor que 0"),
    ({"costos": [[1, 2]], "oferta": [3], "demanda": [1, 2],
      "metodo_inicial": "magia"}, "Método"),
    ({"costos": [[1, 2]], "oferta": [3], "demanda": [1, 2],
      "objetivo": "medio"}, "objetivo"),
    ({"costos": [[1] * 11], "oferta": [11], "demanda": [1] * 11}, "entre 1 y 10"),
    ({"costos": "hola", "oferta": [1], "demanda": [1]}, "obligatoria"),
])
def test_api_transporte_invalidos(cliente, datos, fragmento):
    r = cliente.post("/api/transporte", json=datos)
    assert r.status_code == 400
    assert fragmento in r.get_json()["error"]


def test_api_sin_json(cliente):
    r = cliente.post("/api/transporte", data="no es json", content_type="text/plain")
    assert r.status_code == 400
    assert "JSON" in r.get_json()["error"]


def test_api_json_lista(cliente):
    r = cliente.post("/api/transporte", json=[1, 2, 3])
    assert r.status_code == 400


def test_api_metodo_get_no_permitido(cliente):
    r = cliente.get("/api/transporte")
    assert r.status_code == 405
    assert "error" in r.get_json()


# --- /api/asignacion ---------------------------------------------------------
def test_api_asignacion_taha(cliente):
    r = cliente.post("/api/asignacion", json={"costos": ASIGNACION_TAHA})
    assert r.status_code == 200
    d = r.get_json()
    assert d["costo_total"] == 27
    assert d["asignacion"] == [[0, 1], [1, 0], [2, 2]]
    assert d["verificacion_scipy"]["coincide"] is True
    assert len(d["pasos"]) >= 3


def test_api_asignacion_max_no_cuadrada(cliente):
    d = cliente.post("/api/asignacion",
                     json={"costos": [[5, 8, 1], [3, 7, 4]], "objetivo": "max"}).get_json()
    assert d["costo_total"] == 12  # 5 + 7
    assert d["verificacion_scipy"]["coincide"]


@pytest.mark.parametrize("datos", [
    {}, {"costos": [[1, -1]]}, {"costos": [[1, 2], [3]]},
    {"costos": [[1]], "objetivo": "x"},
])
def test_api_asignacion_invalidos(cliente, datos):
    r = cliente.post("/api/asignacion", json=datos)
    assert r.status_code == 400
    assert "error" in r.get_json()
