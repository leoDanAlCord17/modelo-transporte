"""Paquete ``solver``: algoritmos del modelo de transporte y de asignación.

Módulos:
    balance       – balanceo con origen/destino ficticio.
    iniciales     – Esquina Noroeste, Costo Mínimo y Vogel (VAM).
    optimo        – método de multiplicadores (MODI) con ciclo stepping-stone.
    hungaro       – método húngaro para el modelo de asignación.
    validacion    – validación de entradas de la API.
    verificacion  – verificación cruzada con SciPy.
    transporte    – orquestación completa del modelo de transporte.
"""

from .balance import balancear
from .hungaro import metodo_hungaro
from .iniciales import costo_minimo, esquina_noroeste, vogel
from .optimo import modi
from .transporte import comparar_metodos, resolver_transporte

__all__ = [
    "balancear", "esquina_noroeste", "costo_minimo", "vogel", "modi",
    "metodo_hungaro", "resolver_transporte", "comparar_metodos",
]
