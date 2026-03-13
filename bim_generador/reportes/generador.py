"""
generador.py
------------
Generador de reportes de superficies y métricas del proyecto.

Genera reportes en PDF y/o Excel con:
  - Superficie por unidad y por tipología
  - Superficie total por planta
  - Métricas de eficiencia (ratio circulación/vendible)
  - Cuadro de unidades

Estado: STUB — implementación planificada para Fase 3.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class GeneradorReporte:
    """Genera reportes PDF/Excel del proyecto."""

    def generar_pdf(self, proyecto: "Proyecto", ruta_salida: str) -> None:
        # TODO: implementar en Fase 3
        raise NotImplementedError("GeneradorReporte.generar_pdf — pendiente Fase 3")

    def generar_excel(self, proyecto: "Proyecto", ruta_salida: str) -> None:
        # TODO: implementar en Fase 3
        raise NotImplementedError("GeneradorReporte.generar_excel — pendiente Fase 3")
