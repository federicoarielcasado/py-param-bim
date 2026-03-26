"""
arquitectonico.py
-----------------
Generador de geometría arquitectónica.

Usa GeneradorPlanta para obtener el layout 2D de cada planta del edificio
y expone una API de alto nivel para el resto del sistema.

Sprint 6: implementación completa.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from bim_generador.generadores.planta import GeneradorPlanta, GeometriaPlanta

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class GeneradorArquitectonico:
    """
    Genera la geometría arquitectónica del edificio.

    Uso:
        gen = GeneradorArquitectonico()
        plantas_geom = gen.generar(proyecto)
        planta_geom  = gen.generar_planta(proyecto, planta_idx=0)
    """

    def __init__(self):
        self._gen_planta = GeneradorPlanta()

    def generar(self, proyecto: "Proyecto") -> list[GeometriaPlanta]:
        """
        Genera la geometría de todas las plantas del edificio.

        Returns:
            Lista de GeometriaPlanta, una por planta (mismo orden que edificio.plantas).
        """
        return [
            self._gen_planta.generar(planta, proyecto.lote, proyecto.edificio)
            for planta in proyecto.edificio.plantas
        ]

    def generar_planta(
        self,
        proyecto: "Proyecto",
        planta_idx: int = 0,
    ) -> GeometriaPlanta:
        """
        Genera la geometría de una planta específica por índice.

        Args:
            proyecto:   Proyecto actual.
            planta_idx: Índice de la planta (0 = PB o primera planta).

        Returns:
            GeometriaPlanta de la planta indicada.
        """
        plantas = proyecto.edificio.plantas
        if not plantas:
            raise ValueError("El edificio no tiene plantas configuradas.")
        idx = max(0, min(planta_idx, len(plantas) - 1))
        return self._gen_planta.generar(plantas[idx], proyecto.lote, proyecto.edificio)
