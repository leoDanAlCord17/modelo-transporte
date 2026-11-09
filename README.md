# Modelo de Transporte con Python (Flask + Vercel)

**Práctica N.º 2 – Investigación de Operaciones** · Estudiante: **Leo Álvarez**
**Aplicación:** <https://modelo-transporte-kappa.vercel.app>
**Repositorio:** <https://github.com/leoDanAlCord17/modelo-transporte>

Aplicación web que resuelve el **modelo de transporte** y el **modelo de asignación** mostrando el
**paso a paso**, con la notación del libro de Taha (*Investigación de Operaciones*, 9.ª ed.).

## Funcionalidades

- Solución inicial: **Esquina Noroeste**, **Costo Mínimo** y **Vogel (VAM)**, con cada paso
  (y las penalizaciones de Vogel).
- Solución óptima con el **método de multiplicadores (MODI)**: u, v, costos reducidos, celda
  entrante y ciclo +/− dibujado en cada iteración.
- **Balanceo** automático con origen o destino ficticio.
- **Maximización** de beneficios.
- **Comparación** de los tres métodos iniciales.
- **Modelo de asignación** con el **método húngaro**, paso a paso.
- **Verificación con SciPy** (`linprog` y `linear_sum_assignment`).
- Validación en el cliente y en el servidor (HTTP 400 con mensajes en español).

## Inicio rápido

```powershell
git clone https://github.com/leoDanAlCord17/modelo-transporte.git
cd modelo-transporte
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py                     # http://127.0.0.1:5000
pytest -v                         # 97 pruebas
```

## Despliegue en Vercel

Subir el repositorio a GitHub e importarlo en <https://vercel.com> (detecta Flask solo), o bien:

```powershell
npm i -g vercel
vercel login
vercel --prod
```

## Estructura

```
app.py          rutas Flask y API JSON
solver/         algoritmos (balance, iniciales, optimo, hungaro, validacion, verificacion)
templates/      plantillas Jinja
public/         CSS, JS e imágenes (servidos por la CDN de Vercel)
tests/          pruebas pytest
docs/           documentación completa
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/transporte` | Solución inicial + MODI + verificación |
| POST | `/api/comparar` | Compara los tres métodos iniciales |
| POST | `/api/asignacion` | Método húngaro + verificación |

Documentación completa (teoría, instalación, uso, API y pruebas):
[docs/DOCUMENTACION.md](docs/DOCUMENTACION.md).
