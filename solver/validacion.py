"""Validación de las entradas recibidas por la API.

Todas las funciones lanzan :class:`ErrorValidacion` con un mensaje claro en
español cuando algún dato no es válido. El controlador Flask convierte esa
excepción en una respuesta HTTP 400 ``{"error": "..."}``.
"""

from __future__ import annotations

import math

MIN_DIM = 1
MAX_DIM = 10
MAX_VALOR = 1e9
MAX_NOMBRE = 30

METODOS_VALIDOS = ("noroeste", "costo_minimo", "vogel")
OBJETIVOS_VALIDOS = ("min", "max")


class ErrorValidacion(ValueError):
    """Error de datos de entrada (se responde con HTTP 400)."""


def _numero(valor, donde: str) -> float:
    """Convierte ``valor`` en float no negativo o lanza ErrorValidacion."""
    if isinstance(valor, bool) or valor is None:
        raise ErrorValidacion(f"{donde}: el valor está vacío o no es numérico.")
    if isinstance(valor, str):
        texto = valor.strip().replace(",", ".")
        if not texto:
            raise ErrorValidacion(f"{donde}: el campo está vacío.")
        try:
            valor = float(texto)
        except ValueError:
            raise ErrorValidacion(f"{donde}: «{valor}» no es un número.") from None
    if not isinstance(valor, (int, float)):
        raise ErrorValidacion(f"{donde}: el valor no es numérico.")
    valor = float(valor)
    if not math.isfinite(valor):
        raise ErrorValidacion(f"{donde}: el valor debe ser un número finito.")
    if valor < 0:
        raise ErrorValidacion(f"{donde}: no se admiten valores negativos.")
    if valor > MAX_VALOR:
        raise ErrorValidacion(f"{donde}: el valor es demasiado grande (máximo 1e9).")
    return valor


def validar_matriz(costos, nombre: str = "costos") -> list[list[float]]:
    """Valida una matriz rectangular de números no negativos (1..10 × 1..10)."""
    if not isinstance(costos, list) or not costos:
        raise ErrorValidacion(f"La matriz de {nombre} es obligatoria y no puede estar vacía.")
    if not all(isinstance(f, list) for f in costos):
        raise ErrorValidacion(f"La matriz de {nombre} debe ser una lista de filas.")
    m, n = len(costos), len(costos[0])
    if not (MIN_DIM <= m <= MAX_DIM) or not (MIN_DIM <= n <= MAX_DIM):
        raise ErrorValidacion(
            f"La matriz de {nombre} debe tener entre {MIN_DIM} y {MAX_DIM} filas y columnas.")
    if any(len(f) != n for f in costos):
        raise ErrorValidacion(f"Todas las filas de la matriz de {nombre} deben tener {n} columnas.")
    return [[_numero(v, f"Costo en fila {i + 1}, columna {j + 1}")
             for j, v in enumerate(fila)] for i, fila in enumerate(costos)]


def validar_vector(valores, longitud: int, nombre: str) -> list[float]:
    """Valida un vector (oferta o demanda) de la longitud indicada."""
    if not isinstance(valores, list):
        raise ErrorValidacion(f"La {nombre} debe ser una lista de números.")
    if len(valores) != longitud:
        raise ErrorValidacion(
            f"La {nombre} debe tener {longitud} valores (tiene {len(valores)}).")
    return [_numero(v, f"{nombre.capitalize()} {k + 1}") for k, v in enumerate(valores)]


def validar_nombres(nombres, longitud: int, prefijo: str) -> list[str]:
    """Valida nombres opcionales; si faltan se generan (O1, O2… / D1, D2…)."""
    por_defecto = [f"{prefijo}{k + 1}" for k in range(longitud)]
    if nombres is None:
        return por_defecto
    if not isinstance(nombres, list) or len(nombres) != longitud:
        raise ErrorValidacion(f"Se esperaban {longitud} nombres para {prefijo}.")
    salida = []
    for k, nom in enumerate(nombres):
        texto = str(nom).strip() if nom is not None else ""
        if len(texto) > MAX_NOMBRE:
            raise ErrorValidacion(f"El nombre «{texto[:15]}…» supera {MAX_NOMBRE} caracteres.")
        salida.append(texto or por_defecto[k])
    return salida


def validar_transporte(datos) -> dict:
    """Valida el cuerpo JSON de ``POST /api/transporte``."""
    if not isinstance(datos, dict):
        raise ErrorValidacion("El cuerpo de la petición debe ser un objeto JSON.")
    costos = validar_matriz(datos.get("costos"))
    m, n = len(costos), len(costos[0])
    oferta = validar_vector(datos.get("oferta"), m, "oferta")
    demanda = validar_vector(datos.get("demanda"), n, "demanda")
    if sum(oferta) <= 0:
        raise ErrorValidacion("La oferta total debe ser mayor que 0.")
    if sum(demanda) <= 0:
        raise ErrorValidacion("La demanda total debe ser mayor que 0.")

    metodo = datos.get("metodo_inicial", "vogel")
    if metodo not in METODOS_VALIDOS:
        raise ErrorValidacion(
            "Método inicial no válido. Use: noroeste, costo_minimo o vogel.")
    objetivo = datos.get("objetivo", "min")
    if objetivo not in OBJETIVOS_VALIDOS:
        raise ErrorValidacion("El objetivo debe ser «min» o «max».")

    return {
        "costos": costos, "oferta": oferta, "demanda": demanda,
        "metodo_inicial": metodo, "objetivo": objetivo,
        "nombres_origenes": validar_nombres(datos.get("nombres_origenes"), m, "O"),
        "nombres_destinos": validar_nombres(datos.get("nombres_destinos"), n, "D"),
    }


def validar_asignacion(datos) -> dict:
    """Valida el cuerpo JSON de ``POST /api/asignacion``."""
    if not isinstance(datos, dict):
        raise ErrorValidacion("El cuerpo de la petición debe ser un objeto JSON.")
    costos = validar_matriz(datos.get("costos"))
    objetivo = datos.get("objetivo", "min")
    if objetivo not in OBJETIVOS_VALIDOS:
        raise ErrorValidacion("El objetivo debe ser «min» o «max».")
    n, m = len(costos), len(costos[0])
    return {
        "costos": costos, "objetivo": objetivo,
        "nombres_filas": validar_nombres(datos.get("nombres_filas"), n, "A"),
        "nombres_columnas": validar_nombres(datos.get("nombres_columnas"), m, "T"),
    }
