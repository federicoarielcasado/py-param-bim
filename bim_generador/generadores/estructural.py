"""
estructural.py
--------------
Generador de grilla estructural.

Genera la posición de columnas, vigas y losas según los parámetros
estructurales del edificio (módulo X/Y, sección de columnas, etc.).

Estado: STUB — implementación planificada para Fase 2.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Edificio, ParametrosEstructurales


class GeneradorEstructural:
    """Genera la grilla estructural del edificio."""

    def generar_grilla(self, edificio: "Edificio") -> dict:
        """
        Genera la grilla de columnas y vigas.

        Retorna:
            dict con 'columnas' (list de posiciones XY) y
            'vigas' (list de segmentos entre columnas).
        """
        # TODO: implementar en Fase 2
        raise NotImplementedError("GeneradorEstructural — pendiente Fase 2")
