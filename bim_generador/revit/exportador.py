"""
exportador.py
-------------
Capa de abstracción de la API de Revit.

Recibe la geometría generada por los generadores y la exporta a un
archivo .rvt via pyRevit o RPW (Revit Python Wrapper).

Todos los elementos creados llevan un parámetro de origen "BIMGen_ID"
para trazabilidad (RNF-06).

Estado: STUB — implementación planificada para Fase 3.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class ExportadorRevit:
    """
    Exporta el modelo a Revit.

    Uso previsto:
        exportador = ExportadorRevit()
        exportador.exportar(proyecto, ruta_rvt="output/mi_edificio.rvt")
    """

    def exportar(self, proyecto: "Proyecto", ruta_rvt: str) -> None:
        """Exporta el proyecto completo a un archivo .rvt."""
        # TODO: implementar en Fase 3
        raise NotImplementedError("ExportadorRevit — pendiente Fase 3")
