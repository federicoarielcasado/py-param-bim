"""
arquitectonico.py
-----------------
Generador de geometría arquitectónica.

Genera muros, losas, aberturas, distribución de ambientes y unidades
a partir de los parámetros del motor de parámetros.

Estado: STUB — implementación planificada para Sprint 5-6 (Fase 2).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto, Planta, Unidad


@dataclass
class GeometriaEdificio:
    """Contenedor de geometría generada para un edificio completo."""
    vertices: list   # lista de arrays numpy (a definir en implementación)
    muros: list
    losas: list
    aberturas: list
    metadata: dict


class GeneradorArquitectonico:
    """
    Genera la geometría arquitectónica del edificio a partir del Proyecto.

    Uso:
        gen = GeneradorArquitectonico()
        geom = gen.generar(proyecto)
    """

    def generar(self, proyecto: "Proyecto") -> GeometriaEdificio:
        """Genera la geometría completa del edificio."""
        # TODO: implementar en Fase 2
        raise NotImplementedError("GeneradorArquitectonico — pendiente Fase 2")

    def generar_planta(self, planta: "Planta", lote_frente: float, lote_fondo: float) -> dict:
        """Genera la geometría de una planta individual."""
        # TODO: implementar en Fase 2
        raise NotImplementedError

    def generar_unidad(self, unidad: "Unidad", origen_x: float, origen_y: float) -> dict:
        """Genera la geometría de una unidad funcional."""
        # TODO: implementar en Fase 2
        raise NotImplementedError
