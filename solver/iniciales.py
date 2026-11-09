"""Métodos para obtener una solución básica factible inicial.

Se implementan los tres métodos del libro de Taha (sección 5.3.1):

1. **Esquina Noroeste**
2. **Costo Mínimo**
3. **Aproximación de Vogel (VAM)**

Los tres siguen el mismo esquema general:

    a) se elige una celda (i, j) entre las filas y columnas "activas"
       (no tachadas) según la regla del método;
    b) se asigna x_ij = min(oferta_i, demanda_j);
    c) se actualizan oferta y demanda y se **tacha exactamente una línea**
       (la fila o la columna que quedó satisfecha).

Regla de degeneración (Taha): si la fila y la columna quedan satisfechas a la
vez, *solo se tacha una de ellas*; la otra permanece con oferta/demanda 0 y
más adelante recibirá una asignación de 0 unidades, que es una **variable
básica degenerada**. Como en cada paso se tacha exactamente una línea (y en el
último paso las dos que quedan), siempre se obtienen exactamente
**m + n − 1 variables básicas**, que forman un árbol (no contienen ciclos),
condición necesaria para el método de multiplicadores (MODI).

Regla concreta de tachado usada en el código:
    - si solo queda una fila y una columna: se tachan ambas (último paso);
    - si solo queda una fila activa: se tacha la columna;
    - si solo queda una columna activa: se tacha la fila;
    - si la fila quedó satisfecha (con o sin la columna): se tacha la fila;
    - en otro caso se tacha la columna.
"""

from __future__ import annotations

import numpy as np

from .utilidades import a_lista, numero, tolerancia

NOMBRES_METODOS = {
    "noroeste": "Esquina Noroeste",
    "costo_minimo": "Costo Mínimo",
    "vogel": "Aproximación de Vogel (VAM)",
}


class _Tablero:
    """Estado interno compartido por los tres métodos iniciales."""

    def __init__(self, costos, oferta, demanda):
        self.C = np.asarray(costos, dtype=float)
        self.m, self.n = self.C.shape
        self.s = np.asarray(oferta, dtype=float).copy()  # oferta restante
        self.d = np.asarray(demanda, dtype=float).copy()  # demanda restante
        self.X = np.zeros((self.m, self.n))
        self.basicas: list[tuple[int, int]] = []
        self.filas = [True] * self.m  # filas activas (no tachadas)
        self.cols = [True] * self.n  # columnas activas (no tachadas)
        self.eps = tolerancia(self.s, self.d)
        self.pasos: list[dict] = []

    # -- consultas -------------------------------------------------------
    def filas_activas(self):
        return [i for i in range(self.m) if self.filas[i]]

    def cols_activas(self):
        return [j for j in range(self.n) if self.cols[j]]

    def terminado(self):
        return not self.filas_activas() or not self.cols_activas()

    # -- operación básica ------------------------------------------------
    def asignar(self, i: int, j: int, extra: dict | None = None, motivo: str = ""):
        """Asigna min(s_i, d_j) a la celda (i, j) y tacha una línea."""
        q = min(self.s[i], self.d[j])
        self.X[i, j] = q
        self.basicas.append((i, j))
        self.s[i] -= q
        self.d[j] -= q
        if abs(self.s[i]) <= self.eps:
            self.s[i] = 0.0
        if abs(self.d[j]) <= self.eps:
            self.d[j] = 0.0

        nf, nc = len(self.filas_activas()), len(self.cols_activas())
        fila_ok = self.s[i] == 0.0
        col_ok = self.d[j] == 0.0
        degenerado = False
        if nf == 1 and nc == 1:
            tachado = "ambas"
            self.filas[i] = self.cols[j] = False
        elif nf == 1:
            tachado = "columna"
            self.cols[j] = False
        elif nc == 1:
            tachado = "fila"
            self.filas[i] = False
        elif fila_ok:
            tachado = "fila"
            self.filas[i] = False
            degenerado = col_ok  # la columna queda activa con demanda 0
        else:
            tachado = "columna"
            self.cols[j] = False

        texto = (f"Se asignan {numero(q)} unidades a la celda "
                 f"(fila {i + 1}, columna {j + 1}) con costo {numero(self.C[i, j])}.")
        if motivo:
            texto = motivo + " " + texto
        if tachado == "ambas":
            texto += " Se tachan la última fila y la última columna."
        else:
            texto += f" Se tacha la {tachado} {(i if tachado == 'fila' else j) + 1}."
        if degenerado:
            texto += (" La fila y la columna se agotaron a la vez: solo se tacha la "
                      "fila y la columna queda con demanda 0 (degeneración: "
                      "aparecerá una variable básica con valor 0).")
        if q == 0:
            texto += " Es una variable básica degenerada (valor 0)."

        paso = {
            "numero": len(self.pasos) + 1,
            "celda": [i, j],
            "cantidad": numero(q),
            "costo_unitario": numero(self.C[i, j]),
            "oferta_restante": a_lista(self.s),
            "demanda_restante": a_lista(self.d),
            "tachado": tachado,
            "degenerado": bool(degenerado or q == 0),
            "descripcion": texto,
        }
        if extra:
            paso.update(extra)
        self.pasos.append(paso)

    def resultado(self, metodo: str) -> dict:
        return {
            "metodo": metodo,
            "nombre_metodo": NOMBRES_METODOS[metodo],
            "asignacion": self.X.copy(),
            "basicas": list(self.basicas),
            "costo_total": float((self.C * self.X).sum()),
            "pasos": self.pasos,
        }


def _celda_costo_minimo(t: _Tablero, filas, cols):
    """Elige la celda de menor costo entre las filas y columnas dadas.

    Desempate determinista (documentado):
        1. menor costo unitario;
        2. mayor cantidad asignable min(s_i, d_j);
        3. menor índice de fila;
        4. menor índice de columna.
    """
    mejor, clave_mejor = None, None
    for i in filas:
        for j in cols:
            clave = (t.C[i, j], -min(t.s[i], t.d[j]), i, j)
            if clave_mejor is None or clave < clave_mejor:
                mejor, clave_mejor = (i, j), clave
    return mejor


def esquina_noroeste(costos, oferta, demanda) -> dict:
    """Método de la Esquina Noroeste (Taha, 5.3.1).

    Se parte de la celda superior izquierda (x_11) de la tabla. Se asigna la
    mayor cantidad posible, se tacha la fila o columna satisfecha y se avanza
    a la nueva esquina noroeste de la tabla restante: hacia abajo si se tachó
    la fila, hacia la derecha si se tachó la columna. El método ignora los
    costos, por eso suele dar soluciones iniciales de mayor costo.
    """
    t = _Tablero(costos, oferta, demanda)
    while not t.terminado():
        i, j = t.filas_activas()[0], t.cols_activas()[0]
        t.asignar(i, j, motivo="Esquina noroeste de la tabla restante.")
    return t.resultado("noroeste")


def costo_minimo(costos, oferta, demanda) -> dict:
    """Método del Costo Mínimo (Taha, 5.3.1).

    En cada paso se elige, entre las celdas no tachadas, la de **menor costo
    unitario** y se le asigna la mayor cantidad posible. Se tacha la fila o
    columna satisfecha y se repite.

    Desempate: menor costo → mayor cantidad asignable → menor fila → menor
    columna.
    """
    t = _Tablero(costos, oferta, demanda)
    while not t.terminado():
        i, j = _celda_costo_minimo(t, t.filas_activas(), t.cols_activas())
        t.asignar(i, j, motivo="Celda de menor costo entre las no tachadas.")
    return t.resultado("costo_minimo")


def _penalizacion(valores):
    """Diferencia entre los dos menores valores de una línea."""
    orden = sorted(valores)
    return orden[1] - orden[0]


def vogel(costos, oferta, demanda) -> dict:
    """Método de Aproximación de Vogel, VAM (Taha, 5.3.1).

    Paso 1. Para cada fila y columna activa se calcula la **penalización**:
            diferencia entre los dos costos más pequeños de sus celdas
            no tachadas.
    Paso 2. Se elige la línea con **mayor penalización** y, en ella, la celda
            de menor costo; se asigna la mayor cantidad posible y se tacha la
            línea satisfecha.
    Paso 3. Cuando queda una sola fila o una sola columna activa ya no se
            pueden calcular penalizaciones: las celdas restantes se asignan
            por costo mínimo.

    Desempates (documentados):
        - entre líneas con igual penalización: la que contiene el menor costo;
          luego filas antes que columnas; luego menor índice;
        - dentro de la línea elegida: menor costo → mayor cantidad asignable
          → menor índice.

    Para cada paso se guardan las penalizaciones de filas y columnas
    (``None`` en las líneas tachadas) para poder mostrarlas en la interfaz.
    """
    t = _Tablero(costos, oferta, demanda)
    while not t.terminado():
        filas, cols = t.filas_activas(), t.cols_activas()
        if len(filas) == 1 or len(cols) == 1:
            i, j = _celda_costo_minimo(t, filas, cols)
            t.asignar(i, j, extra={
                "penalizaciones_filas": None,
                "penalizaciones_columnas": None,
                "linea_elegida": None,
            }, motivo=("Queda una sola fila o columna activa: se asigna por "
                       "costo mínimo."))
            continue

        pen_f = [None] * t.m
        pen_c = [None] * t.n
        candidatos = []
        for i in filas:
            vals = [t.C[i, j] for j in cols]
            pen_f[i] = _penalizacion(vals)
            candidatos.append((-pen_f[i], min(vals), 0, i))
        for j in cols:
            vals = [t.C[i, j] for i in filas]
            pen_c[j] = _penalizacion(vals)
            candidatos.append((-pen_c[j], min(vals), 1, j))
        _, _, tipo, k = min(candidatos)

        if tipo == 0:
            i, j = _celda_costo_minimo(t, [k], cols)
            linea = {"tipo": "fila", "indice": k, "penalizacion": numero(pen_f[k])}
        else:
            i, j = _celda_costo_minimo(t, filas, [k])
            linea = {"tipo": "columna", "indice": k, "penalizacion": numero(pen_c[k])}

        t.asignar(i, j, extra={
            "penalizaciones_filas": [numero(p) for p in pen_f],
            "penalizaciones_columnas": [numero(p) for p in pen_c],
            "linea_elegida": linea,
        }, motivo=(f"Mayor penalización = {linea['penalizacion']} en la "
                   f"{linea['tipo']} {k + 1}; se elige su celda de menor costo."))
    return t.resultado("vogel")


METODOS = {
    "noroeste": esquina_noroeste,
    "costo_minimo": costo_minimo,
    "vogel": vogel,
}
