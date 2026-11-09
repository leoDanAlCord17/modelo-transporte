"""Verificación cruzada con SciPy.

Los algoritmos propios (Esquina NO, Costo Mínimo, Vogel, MODI y Húngaro) son
los que se muestran al usuario. SciPy se usa **solo para comprobar** que el
costo óptimo obtenido es correcto:

- transporte → ``scipy.optimize.linprog`` (programación lineal, HiGHS);
- asignación → ``scipy.optimize.linear_sum_assignment``.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import linear_sum_assignment, linprog

from .utilidades import numero


def costos_coinciden(a: float, b: float) -> bool:
    """Compara dos costos con tolerancia relativa y absoluta."""
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)


def linprog_transporte(costos, oferta, demanda) -> float:
    """Costo mínimo de un problema de transporte **balanceado** vía linprog.

    Modelo de PL:
        min  Σ c_ij x_ij
        s.a. Σ_j x_ij = a_i   (oferta de cada origen)
             Σ_i x_ij = b_j   (demanda de cada destino)
             x_ij ≥ 0
    """
    C = np.asarray(costos, dtype=float)
    m, n = C.shape
    A_eq = np.zeros((m + n, m * n))
    for i in range(m):
        A_eq[i, i * n:(i + 1) * n] = 1.0
    for j in range(n):
        A_eq[m + j, j::n] = 1.0
    b_eq = np.concatenate([np.asarray(oferta, float), np.asarray(demanda, float)])
    res = linprog(C.ravel(), A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs")
    if not res.success:  # pragma: no cover
        raise RuntimeError(f"linprog no encontró solución: {res.message}")
    return float(res.fun)


def verificar_transporte(costos_trabajo, oferta, demanda, costo_propio_trabajo,
                         signo: int) -> dict:
    """Compara el óptimo propio (MODI) con linprog.

    ``costos_trabajo`` es la matriz con la que se minimizó (−C si se
    maximiza); ``signo`` = 1 (min) o −1 (max) permite devolver el valor en las
    unidades originales.
    """
    valor = linprog_transporte(costos_trabajo, oferta, demanda)
    return {
        "metodo": "scipy.optimize.linprog (HiGHS)",
        "costo_total": numero(signo * valor),
        "coincide": costos_coinciden(valor, costo_propio_trabajo),
    }


def verificar_asignacion(costos, objetivo: str, costo_propio: float) -> dict:
    """Compara el resultado del método húngaro con linear_sum_assignment."""
    C = np.asarray(costos, dtype=float)
    filas, cols = linear_sum_assignment(C, maximize=(objetivo == "max"))
    valor = float(C[filas, cols].sum())
    return {
        "metodo": "scipy.optimize.linear_sum_assignment",
        "costo_total": numero(valor),
        "coincide": costos_coinciden(valor, costo_propio),
    }
