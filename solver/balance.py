"""Balanceo del modelo de transporte.

El método de transporte (Taha, cap. 5) exige que la oferta total sea igual a
la demanda total. Cuando no ocurre así se agrega:

- un **destino ficticio** (columna) si la oferta supera a la demanda; la
  cantidad asignada a él representa la oferta que *no se envía*;
- un **origen ficticio** (fila) si la demanda supera a la oferta; la cantidad
  asignada desde él representa la demanda *no satisfecha*.

En ambos casos el costo unitario de las celdas ficticias es 0.
"""

from __future__ import annotations

import numpy as np

from .utilidades import tolerancia


def balancear(costos, oferta, demanda) -> dict:
    """Balancea el problema añadiendo un origen o un destino ficticio.

    Parámetros
    ----------
    costos : matriz m×n de costos unitarios.
    oferta : vector de longitud m.
    demanda : vector de longitud n.

    Devuelve
    --------
    dict con las claves:
        ``costos``, ``oferta``, ``demanda`` (arreglos numpy ya balanceados),
        ``balanceado`` (bool: si el problema original ya estaba balanceado),
        ``ficticio`` (``"origen"``, ``"destino"`` o ``None``) y
        ``cantidad_ficticia`` (oferta o demanda agregada).
    """
    C = np.asarray(costos, dtype=float).copy()
    a = np.asarray(oferta, dtype=float).copy()
    b = np.asarray(demanda, dtype=float).copy()
    m, n = C.shape

    diferencia = float(a.sum() - b.sum())
    eps = tolerancia(a, b, [a.sum()])

    if abs(diferencia) <= eps:
        # Ya está balanceado. Se corrige el posible ruido de coma flotante
        # en la última demanda para que las sumas coincidan exactamente.
        b[-1] += diferencia
        return {
            "costos": C, "oferta": a, "demanda": b,
            "balanceado": True, "ficticio": None, "cantidad_ficticia": 0.0,
        }

    if diferencia > 0:
        # Sobra oferta: se agrega un destino ficticio (nueva columna).
        C = np.hstack([C, np.zeros((m, 1))])
        b = np.append(b, diferencia)
        ficticio = "destino"
    else:
        # Falta oferta: se agrega un origen ficticio (nueva fila).
        C = np.vstack([C, np.zeros((1, n))])
        a = np.append(a, -diferencia)
        ficticio = "origen"

    return {
        "costos": C, "oferta": a, "demanda": b,
        "balanceado": False, "ficticio": ficticio,
        "cantidad_ficticia": abs(diferencia),
    }
