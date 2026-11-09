# Práctica N.º 2 — Modelo de Transporte con Python

| | |
|---|---|
| **Asignatura** | Investigación de Operaciones |
| **Práctica** | N.º 2 – Modelo de Transporte con Python (Flask + Vercel) |
| **Estudiante** | Leo Álvarez |
| **Aplicación desplegada** | [LINK] |
| **Repositorio** | [LINK] |
| **Referencia** | H. A. Taha, *Investigación de Operaciones*, 9.ª ed., Pearson. |

[CAPTURA: Página de inicio de la aplicación]

---

## Índice

1. [Introducción](#1-introducción)
2. [Objetivos](#2-objetivos)
3. [Fundamentos teóricos](#3-fundamentos-teóricos)
4. [Tecnologías utilizadas](#4-tecnologías-utilizadas)
5. [Estructura del proyecto](#5-estructura-del-proyecto)
6. [Instalación paso a paso](#6-instalación-paso-a-paso)
7. [Configuración](#7-configuración)
8. [Ejecución local](#8-ejecución-local)
9. [Despliegue en Vercel](#9-despliegue-en-vercel)
10. [Manual de uso con un ejemplo resuelto](#10-manual-de-uso-con-un-ejemplo-resuelto)
11. [API JSON](#11-api-json)
12. [Pruebas realizadas](#12-pruebas-realizadas)
13. [Conclusiones](#13-conclusiones)

---

## 1. Introducción

El **modelo de transporte** es una clase especial de programación lineal que busca la forma más
económica de enviar un bien desde varios **orígenes** (fábricas, silos, almacenes) hasta varios
**destinos** (clientes, molinos, tiendas), respetando la oferta de cada origen y la demanda de
cada destino. El **modelo de asignación** es un caso particular en el que cada origen se asigna
exactamente a un destino.

En esta práctica se desarrolló una aplicación web en Python que resuelve ambos modelos y, sobre
todo, **muestra el paso a paso** de cada método, con la notación del libro de Taha, para que sirva
como herramienta de aprendizaje. La aplicación está publicada gratis en Vercel.

## 2. Objetivos

**Objetivo general.** Implementar en Python, con Flask, una aplicación web que resuelva el
modelo de transporte y el de asignación mostrando cada paso de los algoritmos.

**Objetivos específicos.**

- Implementar los métodos de solución inicial: Esquina Noroeste, Costo Mínimo y Aproximación de Vogel.
- Implementar la búsqueda del óptimo con el método de multiplicadores (MODI) y el ciclo *stepping-stone*.
- Implementar el método húngaro para el modelo de asignación.
- Balancear automáticamente los problemas con orígenes o destinos ficticios.
- Verificar los resultados con SciPy (`linprog` y `linear_sum_assignment`).
- Construir una interfaz intuitiva con formularios HTML, CSS propio y JavaScript (`fetch` + JSON).
- Validar las entradas en el cliente y en el servidor.
- Probar el código con pytest y desplegarlo en Vercel.

## 3. Fundamentos teóricos

### 3.1 Modelo de transporte

Sean *m* orígenes con oferta *aᵢ*, *n* destinos con demanda *bⱼ* y un costo unitario *cᵢⱼ* por
enviar una unidad de *i* a *j*. Las variables *xᵢⱼ* son las cantidades enviadas:

```
minimizar   z = Σᵢ Σⱼ cᵢⱼ xᵢⱼ
sujeto a    Σⱼ xᵢⱼ = aᵢ      i = 1..m   (oferta)
            Σᵢ xᵢⱼ = bⱼ      j = 1..n   (demanda)
            xᵢⱼ ≥ 0
```

**Características.**

- Se representa con la *tabla de transporte*: filas = orígenes, columnas = destinos, costo en la
  esquina de cada celda, oferta a la derecha y demanda abajo.
- El modelo exige **equilibrio**: Σ aᵢ = Σ bⱼ. Si la oferta es mayor, se agrega un **destino
  ficticio**; si la demanda es mayor, un **origen ficticio**. En ambos casos el costo es 0.
- Una solución básica factible tiene exactamente **m + n − 1 variables básicas**. Si alguna vale
  0, la solución es **degenerada**.
- Si ofertas y demandas son enteras, la solución óptima también es entera.

### 3.2 Método de la Esquina Noroeste

1. Empezar en la celda superior izquierda (x₁₁).
2. Asignar la mayor cantidad posible: xᵢⱼ = mín(aᵢ, bⱼ).
3. Restar esa cantidad de la oferta y la demanda y tachar la fila o columna satisfecha.
4. Moverse a la celda de la derecha (si se tachó la columna) o a la de abajo (si se tachó la fila).
5. Si se satisfacen fila y columna a la vez, **se tacha solo una** y la otra recibirá después una
   asignación 0 (variable básica degenerada).

Es simple, pero no considera los costos.

### 3.3 Método del Costo Mínimo

En cada paso se elige, entre las celdas no tachadas, la de **menor costo** y se le asigna la mayor
cantidad posible. Se tacha la línea satisfecha y se repite.

*Desempate usado:* menor costo → mayor cantidad asignable → menor índice de fila → menor índice de
columna.

### 3.4 Método de Aproximación de Vogel (VAM)

1. Para cada fila y columna activa, calcular la **penalización**: diferencia entre sus dos costos
   más pequeños.
2. Elegir la línea con **mayor penalización** y asignar en su celda de menor costo.
3. Tachar la línea satisfecha y recalcular las penalizaciones.
4. Cuando queda una sola fila o columna activa, las celdas restantes se asignan por costo mínimo.

*Desempate usado:* entre penalizaciones iguales, la línea con el menor costo; luego filas antes que
columnas; luego menor índice. VAM suele dar la mejor solución inicial.

### 3.5 Búsqueda de la solución óptima: método de multiplicadores (MODI)

1. Asociar un multiplicador *uᵢ* a cada fila y *vⱼ* a cada columna. Para cada **variable básica**:
   **uᵢ + vⱼ = cᵢⱼ**. Fijando **u₁ = 0** se despejan los demás.
2. Para cada **variable no básica** calcular el costo reducido **dᵢⱼ = cᵢⱼ − uᵢ − vⱼ**.
   (Taha usa uᵢ + vⱼ − cᵢⱼ, que es el mismo número con signo opuesto.)
3. Si todos los dᵢⱼ ≥ 0, la solución es **óptima**. Si no, entra la celda con el dᵢⱼ más negativo.
4. Construir el **ciclo cerrado**: empieza en la celda entrante, recorre celdas básicas con
   movimientos alternos horizontales y verticales y vuelve al inicio. Los signos se alternan
   + − + − empezando en la celda entrante.
5. **θ** = mínimo de las cantidades en las celdas "−". Sumar θ en las "+" y restarlo en las "−".
   Sale de la base una celda "−" que llegó a 0.
6. Volver al paso 1.

**Implementación del ciclo.** Las m + n − 1 celdas básicas forman un *árbol* sobre el grafo
bipartito filas–columnas. Al agregar la celda entrante (i, j) aparece un único ciclo: el camino del
árbol entre la columna j y la fila i más la nueva celda. Ese camino se halla con una búsqueda en
anchura (BFS), lo que asegura encontrar siempre el ciclo correcto.

**Degeneración.** Si la base tiene menos de m + n − 1 celdas, se completa con celdas de valor 0
que no formen ciclos. Ante muchos pivotes con θ = 0 se pasa a la regla de Bland para evitar
ciclar, y hay un límite de seguridad de 500 iteraciones.

**Maximización.** Maximizar Σ cᵢⱼ xᵢⱼ equivale a minimizar Σ (−cᵢⱼ) xᵢⱼ: la aplicación trabaja con
la matriz −C. Los totales se informan con los beneficios originales.

### 3.6 Modelo de asignación

Hay *n* agentes y *n* tareas. Cada agente hace una sola tarea y cada tarea la hace un solo agente:

```
minimizar   Σᵢ Σⱼ cᵢⱼ xᵢⱼ
sujeto a    Σⱼ xᵢⱼ = 1,  Σᵢ xᵢⱼ = 1,  xᵢⱼ ∈ {0, 1}
```

Es un modelo de transporte con todas las ofertas y demandas iguales a 1. Si la matriz no es
cuadrada se agregan filas o columnas ficticias de costo 0.

### 3.7 Método húngaro

1. **Reducción por filas:** restar a cada fila su mínimo.
2. **Reducción por columnas:** restar a cada columna su mínimo.
3. **Cubrir todos los ceros** con el mínimo número de líneas. Si se necesitan *n* líneas, hay una
   asignación óptima formada por *n* ceros independientes.
4. Si no, sea *k* el menor elemento no cubierto: restar *k* a los no cubiertos, sumar *k* a las
   intersecciones de dos líneas y volver al paso 3.

**Implementación.** Para garantizar el número *mínimo* de líneas se usa el **teorema de König**:
se calcula un emparejamiento máximo de ceros (caminos de aumento) y de él se obtiene la cobertura
mínima. **Maximización:** se usa c'ᵢⱼ = máx(C) − cᵢⱼ.

## 4. Tecnologías utilizadas

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje principal |
| Flask | 3.1.3 | Servidor web, rutas y plantillas Jinja |
| NumPy | 2.5.4 | Operaciones con matrices |
| SciPy | 1.18.1 | Verificación con `linprog` y `linear_sum_assignment` |
| pytest | 9.2.0 | Pruebas automatizadas |
| HTML5 + CSS3 | — | Interfaz (CSS propio, sin frameworks) |
| JavaScript | ES2020 | `fetch` + JSON, sin dependencias externas |
| Vercel | — | Despliegue gratuito (Python serverless + CDN) |
| Git / GitHub | — | Control de versiones |

## 5. Estructura del proyecto

```
modelo-transporte/
├── app.py                  # Flask: rutas de páginas, API JSON y manejo de errores
├── solver/                 # Módulo de algoritmos (independiente de Flask)
│   ├── __init__.py
│   ├── balance.py          # balanceo con origen/destino ficticio
│   ├── iniciales.py        # esquina_noroeste, costo_minimo, vogel
│   ├── optimo.py           # MODI / stepping-stone
│   ├── hungaro.py          # método húngaro
│   ├── validacion.py       # validación de entradas
│   ├── verificacion.py     # verificación cruzada con SciPy
│   ├── transporte.py       # orquestación: balanceo → inicial → MODI → verificación
│   └── utilidades.py       # tolerancias y conversión a JSON
├── templates/              # Plantillas Jinja
│   ├── base.html           # estructura común y barra de navegación
│   ├── index.html          # inicio + teoría breve
│   ├── transporte.html
│   ├── asignacion.html
│   ├── documentacion.html
│   └── error.html
├── public/                 # Archivos estáticos (servidos por la CDN de Vercel)
│   ├── css/styles.css
│   ├── img/favicon.svg
│   └── js/
│       ├── comun.js        # utilidades compartidas (DOM, validación, fetch)
│       ├── transporte.js
│       └── asignacion.js
├── tests/                  # Pruebas pytest
│   ├── conftest.py
│   ├── test_iniciales.py
│   ├── test_optimo.py
│   ├── test_hungaro.py
│   └── test_api.py
├── docs/DOCUMENTACION.md
├── requirements.txt        # dependencias de producción (versiones fijadas)
├── requirements-dev.txt    # + pytest
├── .python-version         # 3.12
├── vercel.json
├── .vercelignore
├── .gitignore
└── README.md
```

El módulo `solver` no depende de Flask: se puede usar y probar por separado. `app.py` solo valida,
llama al solver y devuelve JSON.

## 6. Instalación paso a paso

**Requisitos:** Python 3.12, Git y, solo para desplegar por consola, Node.js.

1. **Comprobar Python:**
   ```powershell
   python --version        # Python 3.12.x
   ```
2. **Clonar el repositorio** (o descargar el ZIP):
   ```powershell
   git clone [LINK]
   cd modelo-transporte
   ```
3. **Crear el entorno virtual:**
   ```powershell
   python -m venv .venv
   ```
4. **Activarlo:**
   ```powershell
   .venv\Scripts\activate          # Windows (PowerShell)
   source .venv/bin/activate       # macOS / Linux
   ```
   Si PowerShell bloquea el script, ejecutar una vez:
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
5. **Instalar dependencias:**
   ```powershell
   pip install -r requirements-dev.txt
   ```
   (`requirements.txt` contiene solo lo necesario en producción; `requirements-dev.txt` añade pytest.)

[CAPTURA: Terminal con el entorno virtual activado y pip install completado]

## 7. Configuración

La aplicación no necesita base de datos ni variables de entorno obligatorias.

| Elemento | Descripción |
|---|---|
| `PORT` (opcional) | Puerto local, por defecto 5000. |
| `VERCEL` | La define Vercel automáticamente. Si **no** existe, Flask sirve `public/` para que todo funcione en local. |
| `Flask(__name__, static_folder=None)` | Flask no gestiona estáticos; en Vercel los sirve la CDN desde `public/`. |
| Rutas de estáticos | Siempre absolutas: `/css/styles.css`, `/js/transporte.js`. No se usa `url_for('static', …)`. |
| `.python-version` | Fija Python 3.12 en Vercel. |
| `vercel.json` | `excludeFiles` deja fuera de la función `tests/`, `docs/`, `public/` y `.venv/`. |
| Límites | Matrices de 1 a 10 filas y columnas; valores entre 0 y 10⁹. |

## 8. Ejecución local

```powershell
.venv\Scripts\activate
python app.py
```

Abrir <http://127.0.0.1:5000>. Para ejecutar las pruebas:

```powershell
pytest -v
```

[CAPTURA: Terminal con `python app.py` en ejecución]

## 9. Despliegue en Vercel

Vercel detecta Flask sin configuración adicional porque `app.py` en la raíz define
`app = Flask(__name__)`.

**Opción A – GitHub (recomendada, redespliegue automático en cada `git push`):**

1. Crear un repositorio vacío en GitHub (sin README).
2. Subir el proyecto:
   ```powershell
   git remote add origin https://github.com/<usuario>/modelo-transporte.git
   git branch -M main
   git push -u origin main
   ```
3. En <https://vercel.com> → **Add New → Project** → importar el repositorio → **Deploy**.
4. Copiar la URL `https://<proyecto>.vercel.app`.

**Opción B – CLI:**

```powershell
npm i -g vercel
vercel login
vercel --prod
```

**Comprobación tras el despliegue:**

```bash
curl -X POST https://<proyecto>.vercel.app/api/transporte \
  -H "Content-Type: application/json" \
  -d '{"costos":[[10,2,20,11],[12,7,9,20],[4,14,16,18]],"oferta":[15,25,10],"demanda":[5,15,15,15],"metodo_inicial":"vogel"}'
curl -I https://<proyecto>.vercel.app/css/styles.css      # debe responder 200
```

**Problemas típicos:**

| Síntoma | Causa probable |
|---|---|
| CSS/JS no cargan | Archivos en `static/` en vez de `public/`, o uso de `url_for('static')`. |
| 404 en `/` | La instancia no se llama `app` o el archivo no es `app.py`. |
| Error de build | Versiones de `requirements.txt` o `.python-version` incompatibles. |

[CAPTURA: Panel de Vercel con el despliegue en estado Ready]

## 10. Manual de uso con un ejemplo resuelto

### 10.1 Pantalla de transporte

1. Ir a **Transporte**.
2. Indicar el número de orígenes y destinos (1–10) y pulsar **Generar tabla**.
3. Completar costos, oferta (columna derecha) y demanda (fila inferior). Los nombres son editables.
   Debajo de la demanda se muestra la suma de oferta y demanda para ver si el problema está balanceado.
4. Elegir el método inicial y el objetivo (minimizar / maximizar).
5. Pulsar **Resolver**. **Cargar ejemplo** rellena el problema SunRay y **Limpiar** vacía la tabla.
6. **Comparar los 3 métodos** muestra una tabla con el costo inicial y las iteraciones de cada método.

Si hay campos vacíos, valores no numéricos o negativos, se resaltan en rojo y no se envía nada.

[CAPTURA: Formulario de transporte con el ejemplo cargado]

### 10.2 Ejemplo resuelto: SunRay Transport (Taha)

Tres silos abastecen a cuatro molinos. Costos (\$/camión), oferta y demanda:

|        | Molino 1 | Molino 2 | Molino 3 | Molino 4 | Oferta |
|--------|:-:|:-:|:-:|:-:|:-:|
| Silo 1 | 10 | 2 | 20 | 11 | 15 |
| Silo 2 | 12 | 7 | 9 | 20 | 25 |
| Silo 3 | 4 | 14 | 16 | 18 | 10 |
| Demanda | 5 | 15 | 15 | 15 | 50 = 50 |

El problema está balanceado (oferta = demanda = 50).

**Solución inicial con Vogel** (los índices son fila, columna):

| Paso | Penalizaciones filas | Penalizaciones columnas | Línea elegida | Asignación |
|:-:|---|---|---|---|
| 1 | 8, 2, **10** | 6, 5, 7, 7 | Fila 3 | x₃₁ = 5 |
| 2 | **9**, 2, 2 | —, 5, 7, 7 | Fila 1 | x₁₂ = 15 (se agotan fila 1 y columna 2: degeneración) |
| 3 | —, 2, 2 | —, **7**, 7, 2 | Columna 2 | x₂₂ = 0 (básica degenerada) |
| 4 | —, **11**, 2 | —, —, 7, 2 | Fila 2 | x₂₃ = 15 |
| 5 | — | — | Una sola columna: costo mínimo | x₃₄ = 5 |
| 6 | — | — | Última celda | x₂₄ = 10 |

En el paso 3 hay empate de penalización 7 entre las columnas 2 y 3; gana la columna 2 porque
contiene el menor costo (7 < 9).

Costo inicial = 15·2 + 0·7 + 15·9 + 10·20 + 5·4 + 5·18 = **475**, con 6 = m + n − 1 variables básicas.

**Iteración MODI 1.** Con u₁ = 0: u = (0, 5, 3), v = (1, 2, 4, 15).
Costos reducidos de las no básicas:

|   | M1 | M2 | M3 | M4 |
|---|:-:|:-:|:-:|:-:|
| S1 | 9 | básica | 16 | **−4** |
| S2 | 6 | básica | básica | básica |
| S3 | básica | 9 | 9 | básica |

Entra x₁₄ (d = −4). Ciclo: **+**(1,4) → **−**(2,4) → **+**(2,2) → **−**(1,2).
θ = mín(10, 15) = 10; sale x₂₄. Nuevo costo = 475 − 4·10 = **435**.

**Iteración MODI 2.** u = (0, 5, 7), v = (−3, 2, 4, 11). Todos los dᵢⱼ ≥ 0 → **solución óptima**.

**Plan óptimo (costo 435):**

- Enviar 5 camiones de Silo 1 a Molino 2.
- Enviar 10 camiones de Silo 1 a Molino 4.
- Enviar 10 camiones de Silo 2 a Molino 2.
- Enviar 15 camiones de Silo 2 a Molino 3.
- Enviar 5 camiones de Silo 3 a Molino 1.
- Enviar 5 camiones de Silo 3 a Molino 4.

`scipy.optimize.linprog` también da 435, así que la verificación aparece en verde.

**Comparación de métodos iniciales:**

| Método | Costo inicial | Iteraciones MODI | Costo óptimo |
|---|:-:|:-:|:-:|
| Esquina Noroeste | 520 | 2 | 435 |
| Costo Mínimo | 475 | 1 | 435 |
| Vogel | 475 | 1 | 435 |

> **Nota sobre el valor óptimo.** El enunciado de la práctica indicaba 315 como óptimo esperado.
> Tanto el método MODI (desde los tres métodos iniciales) como `scipy.optimize.linprog` dan
> **435**, que es el valor que publica el libro de Taha para este ejemplo. Por eso se usa 435
> en las pruebas.

[CAPTURA: Resumen de resultados con la verificación de scipy en verde]
[CAPTURA: Paso a paso del método de Vogel con las penalizaciones]
[CAPTURA: Iteración MODI con el ciclo + / − dibujado]
[CAPTURA: Solución óptima y plan de envíos]
[CAPTURA: Tabla comparativa de los tres métodos]

### 10.3 Problemas no balanceados

Si la oferta total es mayor que la demanda, aparece un aviso y una columna **Ficticio**; lo que se
"envía" a ella es la oferta que no se usa. Si la demanda es mayor, aparece una fila **Ficticio** y
lo asignado desde ella es demanda no satisfecha.

[CAPTURA: Aviso de problema no balanceado con destino ficticio]

### 10.4 Ejemplo de asignación (Taha)

Tres niños (Juan, Karen, Terri) y tres tareas (podar, pintar, lavar autos):

|   | Podar | Pintar | Lavar |
|---|:-:|:-:|:-:|
| Juan | 15 | 10 | 9 |
| Karen | 9 | 15 | 10 |
| Terri | 10 | 12 | 8 |

1. Reducción por filas (mínimos 9, 9, 8) → `[[6,1,0],[0,6,1],[2,4,0]]`.
2. Reducción por columnas (mínimos 0, 1, 0) → `[[6,0,0],[0,5,1],[2,3,0]]`.
3. Los ceros se cubren con 3 líneas = n → ya hay asignación óptima.

**Asignación óptima:** Juan → Pintar (10), Karen → Podar (9), Terri → Lavar (8). **Costo = 27**,
igual que `linear_sum_assignment`.

[CAPTURA: Resultado del método húngaro con las celdas asignadas resaltadas]
[CAPTURA: Paso a paso del método húngaro con las líneas de cobertura]

## 11. API JSON

Toda la comunicación entre la interfaz y el servidor usa JSON mediante `fetch`.

### `POST /api/transporte`

**Entrada**

```json
{
  "costos": [[10,2,20,11],[12,7,9,20],[4,14,16,18]],
  "oferta": [15,25,10],
  "demanda": [5,15,15,15],
  "metodo_inicial": "noroeste | costo_minimo | vogel",
  "objetivo": "min | max",
  "nombres_origenes": ["Silo 1","Silo 2","Silo 3"],
  "nombres_destinos": ["Molino 1","Molino 2","Molino 3","Molino 4"]
}
```

`nombres_*` son opcionales. `metodo_inicial` por defecto es `vogel` y `objetivo` es `min`.

**Salida**

| Campo | Descripción |
|---|---|
| `balanceado`, `ficticio`, `cantidad_ficticia` | Resultado del balanceo (`ficticio`: `"origen"`, `"destino"` o `null`). |
| `costos`, `oferta`, `demanda`, `nombres_*` | Datos ya balanceados (con la fila o columna ficticia si la hay). |
| `inicial.metodo`, `inicial.asignacion`, `inicial.basicas`, `inicial.costo_total` | Solución inicial. |
| `inicial.pasos[]` | Cada paso: `celda`, `cantidad`, `oferta_restante`, `demanda_restante`, `tachado`, `descripcion`; en Vogel además `penalizaciones_filas`, `penalizaciones_columnas`, `linea_elegida`. |
| `optimo.asignacion`, `optimo.basicas`, `optimo.costo_total` | Solución óptima. |
| `optimo.iteraciones[]` | `u`, `v`, `costos_reducidos`, `celda_entrante` (`null` en la última), `ciclo`, `signos`, `theta`, `celda_saliente`, `asignacion_resultante`, `costo`. |
| `optimo.envios[]` | Lista legible de envíos (`origen`, `destino`, `cantidad`, `subtotal`, `ficticio`). |
| `verificacion_scipy` | `{ "costo_total", "coincide" }` calculado con `linprog`. |

### `POST /api/comparar`

Mismo cuerpo que `/api/transporte`. Devuelve
`{"metodos": [{"metodo", "nombre_metodo", "costo_inicial", "iteraciones", "costo_optimo"}]}`.

### `POST /api/asignacion`

```json
{ "costos": [[15,10,9],[9,15,10],[10,12,8]], "objetivo": "min" }
```

Devuelve `asignacion` (pares `[fila, columna]`), `costo_total`, `pasos` (cada uno con `tipo`,
`descripcion`, `matriz` y, según el tipo, `minimos`, `filas_cubiertas`, `columnas_cubiertas`, `k`)
y `verificacion_scipy`.

### Errores

| Código | Cuándo | Cuerpo |
|---|---|---|
| 400 | Datos inválidos: vacíos, no numéricos, negativos, dimensiones fuera de 1–10, JSON mal formado | `{"error": "mensaje en español"}` |
| 404 / 405 | Ruta o método inexistente en `/api/*` | `{"error": "..."}` |
| 422 | Se alcanzó el límite de iteraciones de MODI | `{"error": "..."}` |

## 12. Pruebas realizadas

Las pruebas se ejecutan con `pytest -v`. Resultado: **97 pruebas superadas, 0 fallidas**.

[CAPTURA: Salida de `pytest -v` con todas las pruebas superadas]

| Archivo | N.º | Qué verifica |
|---|:-:|---|
| `test_iniciales.py` | 25 | Esquina NO, Costo Mínimo y Vogel; balanceo; degeneración; 1×n, m×1; decimales |
| `test_optimo.py` | 23 | MODI, ciclo, no balanceados, maximización, comparación, prueba aleatoria |
| `test_hungaro.py` | 10 | Método húngaro: ejemplo de Taha, ajustes, maximización, no cuadradas, aleatorias |
| `test_api.py` | 39 | Páginas, estáticos, API JSON y entradas inválidas (400) |

**Casos principales y resultados:**

| Caso | Datos | Esperado | Obtenido |
|---|---|---|---|
| SunRay – Esquina NO | Taha, 3×4 | 520 | 520 ✔ |
| SunRay – Costo Mínimo | Taha, 3×4 | 475 | 475 ✔ |
| SunRay – Vogel | Taha, 3×4 | 475 | 475 ✔ |
| SunRay – Óptimo (3 métodos) | Taha, 3×4 | 435 (linprog) | 435 ✔ |
| SunRay – 1.ª iteración MODI desde Esquina NO | u, v, d₃₁ | u=(0,5,3), v=(10,2,4,15), d₃₁=−9, θ=5 | ✔ |
| Penalizaciones Vogel paso 1 | Taha | filas 8,2,10; columnas 6,5,7,7 | ✔ |
| Oferta > demanda | 3×3, sobran 20 | destino ficticio con 20 | ✔ |
| Demanda > oferta | 2×3 | origen ficticio | ✔ |
| Degenerado | fila y columna se agotan a la vez | m+n−1 básicas, árbol | ✔ |
| 1×n, m×1, 1×1 | casos límite | 17, 17, 35 | ✔ |
| Maximización | beneficios SunRay | = −linprog(−C) | ✔ |
| Decimales | costos y cantidades con decimales | = linprog | ✔ |
| **Aleatorio** | 50 problemas × 3 métodos (semilla 2024), incluye no balanceados y max | MODI = linprog | 150/150 ✔ |
| Asignación Taha | 3×3 | 27 | 27 ✔ |
| Húngaro con ajuste | 5×5 | = linear_sum_assignment | ✔ |
| Húngaro no cuadrado / max | 4×2, 2×4, 3×3 | = linear_sum_assignment | ✔ |
| Húngaro aleatorio | 60 matrices (semilla 7) | = linear_sum_assignment | 60/60 ✔ |
| Entradas inválidas | vacíos, negativos, texto, booleanos, dimensiones, JSON mal formado | HTTP 400 | ✔ |

Además, en cada iteración de MODI se comprueba que las celdas básicas sigan formando un árbol de
m + n − 1 celdas y que la solución respete oferta, demanda y no negatividad.

## 13. Conclusiones

- Se implementaron en Python los tres métodos de solución inicial, el método de multiplicadores
  (MODI) y el método húngaro, mostrando cada paso como en el libro de Taha.
- En el ejemplo SunRay, Vogel y Costo Mínimo parten de 475, más cerca del óptimo (435) que la
  Esquina Noroeste (520), y necesitan menos iteraciones. Esto confirma que conviene usar un
  método inicial que tenga en cuenta los costos.
- Manejar bien la degeneración (mantener siempre m + n − 1 básicas que formen un árbol) es
  indispensable para que MODI funcione. Tratar la base como un árbol permite encontrar el ciclo de
  forma exacta.
- La verificación con SciPy en 150 problemas aleatorios de transporte y 60 de asignación da
  confianza en la corrección de los algoritmos propios.
- Separar el solver de Flask permitió probar los algoritmos de forma independiente y mantener
  `app.py` simple. La comunicación solo en JSON facilita reutilizar la API.
- Vercel permite publicar gratis una aplicación Flask, siempre que los estáticos estén en
  `public/` y se referencien con rutas absolutas.
