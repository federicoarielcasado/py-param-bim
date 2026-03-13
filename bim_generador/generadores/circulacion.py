"""
circulacion.py
--------------
Generador de núcleos de circulación vertical y pasillos.

Genera escaleras, ascensores, pasillos de distribución y calcula
distancias de evacuación.

Estado: STUB — implementación planificada para Fase 2.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Edificio


class GeneradorCirculacion:
    """Genera los núcleos verticales y pasillos horizontales."""

    def generar_nucleos(self, edificio: "Edificio") -> list[dict]:
        """Genera la geometría de los núcleos verticales."""
        # TODO: implementar en Fase 2
        raise NotImplementedError("GeneradorCirculacion — pendiente Fase 2")

    def calcular_distancia_evacuacion(self, planta_geom: dict) -> float:
        """
        Calcula la distancia máxima de evacuación hasta el núcleo vertical.

        Retorna: distancia en metros.
        """
        # TODO: implementar en Fase 2
        raise NotImplementedError
