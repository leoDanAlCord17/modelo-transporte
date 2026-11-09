"""Búsqueda de la solución óptima: método de multiplicadores (MODI).

Algoritmo (Taha, sección 5.3.2, "método de los multiplicadores"):

1. A cada fila i se le asocia un multiplicador u_i y a cada columna j un
   multiplicador v_j. Para cada **variable básica** x_ij se cumple

        u_i + v_j = c_ij

   Hay m + n incógnitas y m + n − 1 ecuaciones, por eso se fija u_1 = 0 y el
   resto se despeja recorriendo las celdas básicas.

2. Para cada **variable no básica** se calcula el costo reducido

        d_ij = c_ij − u_i − v_j

   (Taha lo presenta como u_i + v_j − c_ij; es el mismo número con signo
   cambiado). Si todos los d_ij ≥ 0 la solución es **óptima** (minimización).

3. Si no, entra a la base la celda con el d_ij **más negativo**. Se construye
   el **ciclo cerrado** (stepping-stone) que parte de la celda entrante y
   recorre celdas básicas alternando movimientos horizontales y verticales.
   Las celdas del ciclo se marcan alternadamente con "+" y "−", empezando por
   "+" en la celda entrante.

4. θ = mínimo de x_ij en las celdas "−". Se suma θ en las celdas "+" y se
   resta en las "−". Sale de la base una celda "−" que quedó en 0 (si varias
   quedan en 0, solo sale una y las demás permanecen como básicas degeneradas).

5. Se repite desde el paso 1.

**Búsqueda robusta del ciclo.** Las m + n − 1 celdas básicas forman un árbol
de expansión del grafo bipartito filas–columnas (cada celda básica (i, j) es
una arista entre el nodo fila i y el nodo columna j). Al agregar la celda
entrante (i, j) se forma exactamente **un** ciclo: el camino único en el árbol
entre la columna j y la fila i, más la arista nueva. Ese camino se encuentra
con una búsqueda en anchura (BFS), sin heurísticas.

**Degeneración.** Si la base recibida tiene menos de m + n − 1 celdas o no es
conexa, se completa con celdas de valor 0 (ε) que conectan las componentes sin
formar ciclos, de modo que siempre hay m + n − 1 básicas.

**Ciclado.** Ante muchos pivotes degenerados seguidos (θ = 0) se cambia a la
regla de Bland (primera celda con d_ij < 0), que evita ciclar. Además existe
un límite de iteraciones de seguridad.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from .utilidades import a_lista, celdas, numero, tolerancia

MAX_ITERACIONES = 500


class ErrorIteraciones(RuntimeError):
    """Se alcanzó el límite de iteraciones de seguridad."""


# ---------------------------------------------------------------------------
# Estructura de la base (árbol de celdas básicas)
# ---------------------------------------------------------------------------
def _buscar(padre, x):
    while padre[x] != x:
        padre[x] = padre[padre[x]]
        x = padre[x]
    return x


def completar_base(C, basicas, m, n):
    """Garantiza m + n − 1 celdas básicas que formen un árbol.

    Usa una estructura de conjuntos disjuntos (union-find) sobre los nodos
    fila (0..m−1) y columna (m..m+n−1). Mientras haya más de una componente,
    se agrega como básica degenerada (valor 0) la celda de menor costo que une
    dos componentes distintas.

    Devuelve la lista de celdas agregadas (normalmente vacía).
    """
    padre = list(range(m + n))
    for i, j in basicas:
        a, b = _buscar(padre, i), _buscar(padre, m + j)
        if a != b:
            padre[a] = b
    agregadas = []
    while len(basicas) < m + n - 1:
        mejor = None
        for i in range(m):
            for j in range(n):
                if _buscar(padre, i) != _buscar(padre, m + j):
                    if mejor is None or C[i, j] < C[mejor]:
                        mejor = (i, j)
        if mejor is None:  # pragma: no cover - no debería ocurrir
            break
        i, j = mejor
        padre[_buscar(padre, i)] = _buscar(padre, m + j)
        basicas.append(mejor)
        agregadas.append(mejor)
    return agregadas


def calcular_multiplicadores(C, basicas, m, n):
    """Resuelve u_i + v_j = c_ij en las celdas básicas con u_1 = 0.

    Se recorre el árbol de básicas en anchura: conocida u_i se obtiene
    v_j = c_ij − u_i para cada básica de la fila i, y conocida v_j se obtiene
    u_i = c_ij − v_j para cada básica de la columna j.
    """
    por_fila = [[] for _ in range(m)]
    por_col = [[] for _ in range(n)]
    for i, j in basicas:
        por_fila[i].append(j)
        por_col[j].append(i)

    u = [None] * m
    v = [None] * n
    u[0] = 0.0
    cola = deque([("fila", 0)])
    while cola:
        tipo, k = cola.popleft()
        if tipo == "fila":
            for j in por_fila[k]:
                if v[j] is None:
                    v[j] = C[k, j] - u[k]
                    cola.append(("col", j))
        else:
            for i in por_col[k]:
                if u[i] is None:
                    u[i] = C[i, k] - v[k]
                    cola.append(("fila", i))
    if any(x is None for x in u) or any(x is None for x in v):  # pragma: no cover
        raise ValueError("La base no es conexa: no se pueden calcular u y v.")
    return np.array(u), np.array(v)


def encontrar_ciclo(basicas, entrante, m, n):
    """Encuentra el ciclo cerrado que forma la celda ``entrante`` con la base.

    Devuelve la lista ordenada de celdas del ciclo, empezando por la entrante.
    Las posiciones pares (0, 2, 4, …) llevan signo "+" y las impares "−".
    """
    ie, je = entrante
    # Grafo bipartito: nodo fila i -> i ; nodo columna j -> m + j
    ady = [[] for _ in range(m + n)]
    for i, j in basicas:
        ady[i].append(m + j)
        ady[m + j].append(i)

    origen, destino = m + je, ie  # camino de la columna j a la fila i
    previo = {origen: None}
    cola = deque([origen])
    while cola:
        x = cola.popleft()
        if x == destino:
            break
        for y in ady[x]:
            if y not in previo:
                previo[y] = x
                cola.append(y)
    if destino not in previo:  # pragma: no cover - la base es un árbol
        raise ValueError("No se encontró un ciclo para la celda entrante.")

    # Reconstruye el camino columna je -> ... -> fila ie
    camino = []
    x = destino
    while x is not None:
        camino.append(x)
        x = previo[x]
    camino.reverse()

    ciclo = [(ie, je)]
    for a, b in zip(camino, camino[1:]):
        # cada arista une un nodo fila con un nodo columna
        if a < m:
            ciclo.append((a, b - m))
        else:
            ciclo.append((b, a - m))
    return ciclo


# ---------------------------------------------------------------------------
# Método MODI
# ---------------------------------------------------------------------------
def modi(costos, asignacion, basicas, max_iter: int = MAX_ITERACIONES) -> dict:
    """Mejora una solución básica factible hasta el óptimo (minimización).

    Parámetros
    ----------
    costos : matriz m×n de costos (ya balanceada).
    asignacion : matriz m×n de la solución inicial.
    basicas : lista de celdas básicas (i, j) de la solución inicial.

    Devuelve
    --------
    dict con ``asignacion`` (óptima), ``basicas``, ``costo_total`` e
    ``iteraciones``. Cada iteración contiene u, v, costos reducidos, celda
    entrante, ciclo con signos, θ, celda saliente, y la asignación resultante.
    La última iteración es la que comprueba la optimalidad
    (``celda_entrante = None``).
    """
    C = np.asarray(costos, dtype=float)
    X = np.asarray(asignacion, dtype=float).copy()
    m, n = C.shape
    basicas = [tuple(c) for c in basicas]
    agregadas = completar_base(C, basicas, m, n)
    tol = tolerancia(C)
    eps_x = tolerancia(X)

    iteraciones = []
    racha_degenerada = 0
    for k in range(max_iter + 1):
        u, v = calcular_multiplicadores(C, basicas, m, n)
        D = C - u[:, None] - v[None, :]
        es_basica = np.zeros((m, n), dtype=bool)
        for i, j in basicas:
            es_basica[i, j] = True
        D[es_basica] = 0.0
        D[np.abs(D) <= tol] = 0.0

        registro = {
            "numero": k + 1,
            "u": a_lista(u),
            "v": a_lista(v),
            "costos_reducidos": a_lista(D),
            "basicas": celdas(basicas),
            "asignacion": a_lista(X),
            "costo_actual": numero((C * X).sum()),
        }

        negativos = [(i, j) for i in range(m) for j in range(n)
                     if not es_basica[i, j] and D[i, j] < -tol]
        if not negativos:
            registro.update({
                "celda_entrante": None, "ciclo": [], "signos": [],
                "theta": None, "celda_saliente": None,
                "asignacion_resultante": a_lista(X),
                "costo": numero((C * X).sum()),
                "optima": True,
                "descripcion": ("Todos los costos reducidos de las celdas no "
                                "básicas son ≥ 0: la solución es óptima."),
            })
            iteraciones.append(registro)
            return {
                "asignacion": X,
                "basicas": basicas,
                "costo_total": float((C * X).sum()),
                "iteraciones": iteraciones,
                "basicas_agregadas": celdas(agregadas),
            }

        if k == max_iter:
            break

        # Regla de entrada: el costo reducido más negativo (Dantzig). Tras
        # muchos pivotes degenerados seguidos se usa la regla de Bland.
        if racha_degenerada > m * n:
            entrante = negativos[0]
            regla = "regla de Bland (anticiclado)"
        else:
            entrante = min(negativos, key=lambda c: (D[c], c))
            regla = "costo reducido más negativo"

        ciclo = encontrar_ciclo(basicas, entrante, m, n)
        menos = ciclo[1::2]
        theta = min(X[c] for c in menos)
        saliente = next(c for c in menos if X[c] <= theta + eps_x)

        for idx, (i, j) in enumerate(ciclo):
            X[i, j] += theta if idx % 2 == 0 else -theta
            if abs(X[i, j]) <= eps_x:
                X[i, j] = 0.0
        X[saliente] = 0.0
        basicas.remove(saliente)
        basicas.append(entrante)
        racha_degenerada = racha_degenerada + 1 if theta <= eps_x else 0

        ie, je = entrante
        registro.update({
            "celda_entrante": [ie, je],
            "ciclo": celdas(ciclo),
            "signos": ["+" if idx % 2 == 0 else "-" for idx in range(len(ciclo))],
            "theta": numero(theta),
            "celda_saliente": [saliente[0], saliente[1]],
            "asignacion_resultante": a_lista(X),
            "costo": numero((C * X).sum()),
            "optima": False,
            "descripcion": (
                f"Entra x({ie + 1},{je + 1}) con costo reducido "
                f"{numero(D[ie, je])} ({regla}). θ = {numero(theta)}; sale "
                f"x({saliente[0] + 1},{saliente[1] + 1})."
                + (" Pivote degenerado (θ = 0)." if theta <= eps_x else "")
            ),
        })
        iteraciones.append(registro)

    raise ErrorIteraciones(
        f"Se alcanzó el límite de {max_iter} iteraciones sin llegar al óptimo.")
