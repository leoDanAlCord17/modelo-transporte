"""Modelo de asignación: Método Húngaro (Taha, sección 5.4.1).

El modelo de asignación es un caso especial del de transporte en el que cada
"trabajador" (fila) se asigna a exactamente una "tarea" (columna). El método
húngaro lo resuelve así:

1. **Matriz cuadrada.** Si hay más filas que columnas (o al revés) se agregan
   columnas (filas) ficticias con costo 0.
2. **Reducción por filas.** A cada fila se le resta su mínimo.
3. **Reducción por columnas.** A cada columna se le resta su mínimo.
4. **Cubrir ceros.** Se cubren todos los ceros con el **mínimo número de
   líneas** (filas o columnas). Si se necesitan n líneas, existe una
   asignación óptima formada por n ceros independientes.
5. **Ajuste.** Si hay menos de n líneas, se toma el menor elemento no cubierto
   k; se resta k a todos los elementos no cubiertos y se suma k a los que
   están en la intersección de dos líneas. Se vuelve al paso 4.

**Maximización.** Se convierte en minimización restando cada elemento del
máximo de la matriz: c'_ij = max(C) − c_ij.

Para obtener el mínimo de líneas se usa el teorema de König: se calcula un
emparejamiento máximo entre filas y columnas usando solo ceros (caminos de
aumento) y, a partir de él, la cobertura mínima de vértices. Así la cobertura
es siempre mínima, sin depender de heurísticas "a ojo".
"""

from __future__ import annotations

import numpy as np

from .utilidades import a_lista, numero, tolerancia

MAX_AJUSTES = 1000


def _emparejamiento_maximo(es_cero):
    """Emparejamiento máximo filas–columnas usando solo celdas con cero.

    Algoritmo de caminos de aumento (Kuhn). Devuelve ``fila_de_col`` donde
    ``fila_de_col[j]`` es la fila emparejada con la columna j (o -1).
    """
    n_f, n_c = es_cero.shape
    fila_de_col = [-1] * n_c

    def aumentar(i, visitadas):
        for j in range(n_c):
            if es_cero[i, j] and not visitadas[j]:
                visitadas[j] = True
                if fila_de_col[j] == -1 or aumentar(fila_de_col[j], visitadas):
                    fila_de_col[j] = i
                    return True
        return False

    for i in range(n_f):
        aumentar(i, [False] * n_c)
    return fila_de_col


def _cobertura_minima(es_cero, fila_de_col):
    """Cobertura mínima de ceros con líneas (teorema de König).

    Desde las filas sin emparejar se recorren caminos alternantes
    (fila → columna por un cero, columna → fila por el emparejamiento).
    Sea Z el conjunto de nodos alcanzados. La cobertura mínima es:
    filas NO alcanzadas  ∪  columnas alcanzadas.
    """
    n = es_cero.shape[0]
    col_de_fila = [-1] * n
    for j, i in enumerate(fila_de_col):
        if i != -1:
            col_de_fila[i] = j

    filas_z = set(i for i in range(n) if col_de_fila[i] == -1)
    cols_z = set()
    pila = list(filas_z)
    while pila:
        i = pila.pop()
        for j in range(n):
            if es_cero[i, j] and j not in cols_z:
                cols_z.add(j)
                k = fila_de_col[j]
                if k != -1 and k not in filas_z:
                    filas_z.add(k)
                    pila.append(k)
    filas_cubiertas = sorted(set(range(n)) - filas_z)
    cols_cubiertas = sorted(cols_z)
    return filas_cubiertas, cols_cubiertas


def metodo_hungaro(costos, objetivo: str = "min") -> dict:
    """Resuelve el modelo de asignación con el método húngaro.

    Parámetros
    ----------
    costos : matriz n×m (filas = agentes, columnas = tareas).
    objetivo : ``"min"`` (costos) o ``"max"`` (beneficios).

    Devuelve
    --------
    dict con ``asignacion`` (lista de pares [fila, columna] reales),
    ``costo_total`` (calculado con la matriz original), ``pasos`` (cada paso
    con la matriz intermedia) y datos auxiliares para la interfaz.
    """
    C0 = np.asarray(costos, dtype=float)
    nf, nc = C0.shape
    N = max(nf, nc)
    pasos = []

    if objetivo == "max":
        maximo = float(C0.max())
        M = maximo - C0
        pasos.append({
            "tipo": "conversion",
            "titulo": "Conversión a minimización",
            "descripcion": (f"Problema de maximización: se resta cada elemento "
                            f"del máximo de la matriz ({numero(maximo)}), "
                            f"c'ij = {numero(maximo)} − cij."),
            "matriz": a_lista(M),
        })
    else:
        M = C0.copy()

    if nf != nc:
        P = np.zeros((N, N))
        P[:nf, :nc] = M
        M = P
        que = "columnas" if nf > nc else "filas"
        pasos.append({
            "tipo": "ficticios",
            "titulo": "Completar matriz cuadrada",
            "descripcion": (f"La matriz es {nf}×{nc}: se agregan {abs(nf - nc)} "
                            f"{que} ficticias con costo 0 para obtener una "
                            f"matriz {N}×{N}."),
            "matriz": a_lista(M),
        })

    tol = tolerancia(M)

    minimos_f = M.min(axis=1)
    M = M - minimos_f[:, None]
    M[np.abs(M) <= tol] = 0.0
    pasos.append({
        "tipo": "reduccion_filas",
        "titulo": "Reducción por filas",
        "descripcion": "A cada fila se le resta su elemento mínimo.",
        "minimos": a_lista(minimos_f),
        "matriz": a_lista(M),
    })

    minimos_c = M.min(axis=0)
    M = M - minimos_c[None, :]
    M[np.abs(M) <= tol] = 0.0
    pasos.append({
        "tipo": "reduccion_columnas",
        "titulo": "Reducción por columnas",
        "descripcion": "A cada columna se le resta su elemento mínimo.",
        "minimos": a_lista(minimos_c),
        "matriz": a_lista(M),
    })

    for _ in range(MAX_AJUSTES):
        es_cero = np.abs(M) <= tol
        fila_de_col = _emparejamiento_maximo(es_cero)
        filas_c, cols_c = _cobertura_minima(es_cero, fila_de_col)
        lineas = len(filas_c) + len(cols_c)
        pasos.append({
            "tipo": "cobertura",
            "titulo": f"Cubrir ceros: {lineas} línea(s)",
            "descripcion": (
                f"Se cubren todos los ceros con el mínimo número de líneas: "
                f"{lineas}. " + (
                    f"Como {lineas} = {N}, existe una asignación óptima."
                    if lineas == N else
                    f"Como {lineas} < {N}, hay que ajustar la matriz.")),
            "filas_cubiertas": filas_c,
            "columnas_cubiertas": cols_c,
            "lineas": lineas,
            "matriz": a_lista(M),
        })
        if lineas == N:
            break

        cub_f = np.zeros(N, dtype=bool)
        cub_f[filas_c] = True
        cub_c = np.zeros(N, dtype=bool)
        cub_c[cols_c] = True
        no_cubiertas = ~cub_f[:, None] & ~cub_c[None, :]
        dobles = cub_f[:, None] & cub_c[None, :]
        k = float(M[no_cubiertas].min())
        M = M.copy()
        M[no_cubiertas] -= k
        M[dobles] += k
        M[np.abs(M) <= tol] = 0.0
        pasos.append({
            "tipo": "ajuste",
            "titulo": f"Ajuste con k = {numero(k)}",
            "descripcion": (f"El menor elemento no cubierto es k = {numero(k)}. "
                            f"Se resta a los no cubiertos y se suma a las "
                            f"intersecciones de dos líneas."),
            "k": numero(k),
            "filas_cubiertas": filas_c,
            "columnas_cubiertas": cols_c,
            "matriz": a_lista(M),
        })
    else:  # pragma: no cover
        raise RuntimeError("El método húngaro superó el límite de ajustes.")

    # Asignación final: el emparejamiento perfecto de ceros
    pares_todos = sorted((fila_de_col[j], j) for j in range(N))
    pares = [[i, j] for i, j in pares_todos if i < nf and j < nc]
    ficticios = [[i, j] for i, j in pares_todos if i >= nf or j >= nc]
    costo = float(sum(C0[i, j] for i, j in pares))
    pasos.append({
        "tipo": "asignacion",
        "titulo": "Asignación óptima",
        "descripcion": ("Se elige un cero en cada fila y columna (ceros "
                        "independientes). Esa es la asignación óptima."),
        "seleccion": [[int(i), int(j)] for i, j in pares_todos],
        "matriz": a_lista(M),
    })

    return {
        "asignacion": pares,
        "asignacion_ficticia": ficticios,
        "costo_total": numero(costo),
        "pasos": pasos,
        "dimension": N,
    }
