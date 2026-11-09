"""Orquestación completa del modelo de transporte.

Une las piezas del paquete:
    balanceo → solución inicial → MODI → verificación con SciPy
y arma la respuesta JSON que consume la interfaz.

**Maximización.** Si el objetivo es maximizar (beneficios), se trabaja con la
matriz C' = −C y se minimiza: maximizar Σ c_ij x_ij equivale a minimizar
Σ (−c_ij) x_ij. Los costos reducidos, u y v de las iteraciones se refieren a
esa matriz de trabajo; los totales se informan siempre con la matriz original.
"""

from __future__ import annotations

import numpy as np

from .balance import balancear
from .iniciales import METODOS, NOMBRES_METODOS
from .optimo import modi
from .utilidades import a_lista, celdas, numero
from .verificacion import verificar_transporte


def _preparar(costos, oferta, demanda, objetivo):
    signo = 1 if objetivo == "min" else -1
    bal = balancear(costos, oferta, demanda)
    C_original = bal["costos"]          # costos/beneficios originales (+ ficticio 0)
    C_trabajo = signo * C_original      # matriz que se minimiza
    return bal, C_original, C_trabajo, signo


def _resolver_con(metodo, C_trabajo, bal):
    inicial = METODOS[metodo](C_trabajo, bal["oferta"], bal["demanda"])
    optimo = modi(C_trabajo, inicial["asignacion"], inicial["basicas"])
    return inicial, optimo


def resolver_transporte(costos, oferta, demanda, metodo_inicial="vogel",
                        objetivo="min", nombres_origenes=None,
                        nombres_destinos=None) -> dict:
    """Resuelve un problema de transporte y devuelve todos los pasos.

    La estructura de la respuesta está documentada en docs/DOCUMENTACION.md
    (sección «API JSON»).
    """
    m, n = len(costos), len(costos[0])
    nombres_origenes = list(nombres_origenes or [f"O{i + 1}" for i in range(m)])
    nombres_destinos = list(nombres_destinos or [f"D{j + 1}" for j in range(n)])

    bal, C_original, C_trabajo, signo = _preparar(costos, oferta, demanda, objetivo)
    if bal["ficticio"] == "origen":
        nombres_origenes.append("Ficticio")
    elif bal["ficticio"] == "destino":
        nombres_destinos.append("Ficticio")

    inicial, optimo = _resolver_con(metodo_inicial, C_trabajo, bal)

    def total(X):
        return numero((C_original * np.asarray(X, dtype=float)).sum())

    # Los pasos muestran el costo/beneficio original de la celda.
    for paso in inicial["pasos"]:
        i, j = paso["celda"]
        paso["costo_unitario"] = numero(C_original[i, j])

    for it in optimo["iteraciones"]:
        it["costo"] = total(it["asignacion_resultante"])
        it["costo_actual"] = total(it["asignacion"])

    X_opt = optimo["asignacion"]
    filas_reales = m
    cols_reales = n
    envios = []
    for i in range(X_opt.shape[0]):
        for j in range(X_opt.shape[1]):
            if X_opt[i, j] > 0:
                envios.append({
                    "origen": nombres_origenes[i],
                    "destino": nombres_destinos[j],
                    "fila": i, "columna": j,
                    "cantidad": numero(X_opt[i, j]),
                    "costo_unitario": numero(C_original[i, j]),
                    "subtotal": numero(C_original[i, j] * X_opt[i, j]),
                    "ficticio": bool(i >= filas_reales or j >= cols_reales),
                })

    verificacion = verificar_transporte(
        C_trabajo, bal["oferta"], bal["demanda"], optimo["costo_total"], signo)

    return {
        "objetivo": objetivo,
        "balanceado": bal["balanceado"],
        "ficticio": bal["ficticio"],
        "cantidad_ficticia": numero(bal["cantidad_ficticia"]),
        "costos": a_lista(C_original),
        "oferta": a_lista(bal["oferta"]),
        "demanda": a_lista(bal["demanda"]),
        "nombres_origenes": nombres_origenes,
        "nombres_destinos": nombres_destinos,
        "inicial": {
            "metodo": metodo_inicial,
            "nombre_metodo": NOMBRES_METODOS[metodo_inicial],
            "asignacion": a_lista(inicial["asignacion"]),
            "basicas": celdas(inicial["basicas"]),
            "costo_total": total(inicial["asignacion"]),
            "pasos": inicial["pasos"],
        },
        "optimo": {
            "asignacion": a_lista(X_opt),
            "basicas": celdas(optimo["basicas"]),
            "costo_total": total(X_opt),
            "iteraciones": optimo["iteraciones"],
            "numero_iteraciones": len(optimo["iteraciones"]) - 1,
            "basicas_agregadas": optimo["basicas_agregadas"],
            "envios": envios,
        },
        "verificacion_scipy": verificacion,
    }


def comparar_metodos(costos, oferta, demanda, objetivo="min") -> dict:
    """Resuelve el problema con los tres métodos iniciales y los compara.

    Para cada método devuelve el costo inicial, el número de iteraciones MODI
    necesarias para llegar al óptimo y el costo óptimo.
    """
    bal, C_original, C_trabajo, signo = _preparar(costos, oferta, demanda, objetivo)
    filas = []
    for metodo in METODOS:
        inicial, optimo = _resolver_con(metodo, C_trabajo, bal)
        filas.append({
            "metodo": metodo,
            "nombre_metodo": NOMBRES_METODOS[metodo],
            "costo_inicial": numero((C_original * inicial["asignacion"]).sum()),
            "iteraciones": len(optimo["iteraciones"]) - 1,
            "costo_optimo": numero((C_original * optimo["asignacion"]).sum()),
        })
    return {"objetivo": objetivo, "ficticio": bal["ficticio"], "metodos": filas}
