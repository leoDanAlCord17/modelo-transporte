"""Aplicación Flask – Práctica N.º 2: Modelo de Transporte con Python.

Rutas de páginas (HTML, plantillas Jinja en ``templates/``):
    GET  /                 inicio y fundamentos teóricos
    GET  /transporte       formulario del modelo de transporte
    GET  /asignacion       formulario del modelo de asignación
    GET  /documentacion    guía de uso y descripción de la API

Rutas de la API (solo JSON):
    POST /api/transporte   solución inicial + MODI + verificación scipy
    POST /api/comparar     compara los tres métodos iniciales
    POST /api/asignacion   método húngaro + verificación scipy

Archivos estáticos: viven en ``public/`` y se referencian con rutas absolutas
(``/css/styles.css``, ``/js/transporte.js``). En Vercel los sirve la CDN
directamente; en local (sin la variable de entorno ``VERCEL``) se registra
una ruta auxiliar que los sirve con ``send_from_directory``.

No hay base de datos ni estado en el servidor: cada petición es independiente.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.exceptions import HTTPException

from solver.hungaro import metodo_hungaro
from solver.optimo import ErrorIteraciones
from solver.transporte import comparar_metodos, resolver_transporte
from solver.validacion import ErrorValidacion, validar_asignacion, validar_transporte
from solver.verificacion import verificar_asignacion

DIRECTORIO_PUBLICO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

# static_folder=None: Flask no sirve estáticos (en Vercel lo hace la CDN).
app = Flask(__name__, static_folder=None)
app.json.ensure_ascii = False  # tildes y eñes legibles en el JSON
app.json.sort_keys = False


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------
@app.get("/")
def inicio():
    return render_template("index.html", activa="inicio")


@app.get("/transporte")
def pagina_transporte():
    return render_template("transporte.html", activa="transporte")


@app.get("/asignacion")
def pagina_asignacion():
    return render_template("asignacion.html", activa="asignacion")


@app.get("/documentacion")
def pagina_documentacion():
    return render_template("documentacion.html", activa="documentacion")


# ---------------------------------------------------------------------------
# API JSON
# ---------------------------------------------------------------------------
def _leer_json():
    """Obtiene el cuerpo JSON o lanza ErrorValidacion si no es válido."""
    datos = request.get_json(silent=True)
    if datos is None:
        raise ErrorValidacion(
            "La petición debe enviar un cuerpo JSON válido "
            "(cabecera Content-Type: application/json).")
    return datos


@app.post("/api/transporte")
def api_transporte():
    """Resuelve un problema de transporte y devuelve el paso a paso."""
    d = validar_transporte(_leer_json())
    resultado = resolver_transporte(
        d["costos"], d["oferta"], d["demanda"],
        metodo_inicial=d["metodo_inicial"], objetivo=d["objetivo"],
        nombres_origenes=d["nombres_origenes"], nombres_destinos=d["nombres_destinos"],
    )
    return jsonify(resultado)


@app.post("/api/comparar")
def api_comparar():
    """Compara Esquina NO, Costo Mínimo y Vogel sobre el mismo problema."""
    d = validar_transporte(_leer_json())
    return jsonify(comparar_metodos(d["costos"], d["oferta"], d["demanda"], d["objetivo"]))


@app.post("/api/asignacion")
def api_asignacion():
    """Resuelve un problema de asignación con el método húngaro."""
    d = validar_asignacion(_leer_json())
    r = metodo_hungaro(d["costos"], d["objetivo"])
    r["objetivo"] = d["objetivo"]
    r["costos"] = d["costos"]
    r["nombres_filas"] = d["nombres_filas"]
    r["nombres_columnas"] = d["nombres_columnas"]
    r["verificacion_scipy"] = verificar_asignacion(d["costos"], d["objetivo"], r["costo_total"])
    return jsonify(r)


# ---------------------------------------------------------------------------
# Manejo de errores: en /api/* siempre se responde JSON
# ---------------------------------------------------------------------------
@app.errorhandler(ErrorValidacion)
def error_validacion(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(ErrorIteraciones)
def error_iteraciones(e):
    return jsonify({"error": str(e)}), 422


@app.errorhandler(HTTPException)
def error_http(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": e.description}), e.code
    return render_template("error.html", codigo=e.code, mensaje=e.description), e.code


@app.errorhandler(Exception)
def error_interno(e):  # pragma: no cover - errores inesperados
    app.logger.exception("Error no controlado")
    if request.path.startswith("/api/"):
        return jsonify({"error": "Error interno del servidor."}), 500
    return render_template("error.html", codigo=500,
                           mensaje="Error interno del servidor."), 500


# ---------------------------------------------------------------------------
# Estáticos SOLO en desarrollo local
# ---------------------------------------------------------------------------
if not os.environ.get("VERCEL"):
    @app.get("/<any(css, js, img):carpeta>/<path:archivo>")
    def estaticos_locales(carpeta, archivo):
        """Sirve ``public/css``, ``public/js`` y ``public/img`` en local.

        En Vercel no se registra: la CDN sirve ``public/`` directamente.
        """
        return send_from_directory(os.path.join(DIRECTORIO_PUBLICO, carpeta), archivo)


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=puerto)
