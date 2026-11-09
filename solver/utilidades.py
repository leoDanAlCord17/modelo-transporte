"""Utilidades comunes del paquete ``solver``.

Contiene funciones pequeñas para:
- calcular una tolerancia numérica proporcional a la escala de los datos,
- convertir arreglos de numpy a estructuras de Python serializables en JSON
  (listas, ``int`` y ``float``), limpiando el "ruido" de coma flotante.
"""

from __future__ import annotations

import math

import numpy as np

# Número de decimales con que se redondean los resultados que se devuelven al
# cliente. Elimina valores como 14.999999999999998 producidos por la aritmética
# de coma flotante.
DECIMALES_SALIDA = 9


def tolerancia(*arreglos) -> float:
    """Devuelve una tolerancia relativa a la magnitud de los datos.

    Se usa para decidir cuándo un número "es cero" (por ejemplo, una oferta
    agotada o un costo reducido nulo) sin depender de igualdades exactas en
    coma flotante.
    """
    escala = 1.0
    for arr in arreglos:
        a = np.asarray(arr, dtype=float)
        if a.size:
            escala = max(escala, float(np.max(np.abs(a))))
    return 1e-9 * escala


def numero(x):
    """Convierte un escalar a ``int`` si es entero, o a ``float`` redondeado."""
    if x is None:
        return None
    x = float(x)
    if not math.isfinite(x):
        return x
    r = round(x, DECIMALES_SALIDA)
    if r == 0:
        return 0  # evita "-0.0"
    if abs(r - round(r)) < 10 ** (-DECIMALES_SALIDA):
        return int(round(r))
    return r


def a_lista(arr):
    """Convierte un vector o matriz de numpy en listas anidadas limpias."""
    a = np.asarray(arr, dtype=float)
    if a.ndim == 1:
        return [numero(x) for x in a]
    return [[numero(x) for x in fila] for fila in a]


def celdas(lista):
    """Convierte una colección de tuplas ``(i, j)`` en listas ``[i, j]``."""
    return [[int(i), int(j)] for i, j in lista]
