"""
fachada.py
----------
Generador de fachadas y balcones.

Genera la geometría de fachadas (aberturas, balcones, materialidad)
a partir de los parámetros del edificio.

Estado: STUB — implementación planificada para Fase 2.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Edificio


class GeneradorFachada:
    """Genera la geometría de fachadas del edificio."""

    def generar_fachada_frontal(self, edificio: "Edificio") -> dict:
        """Genera la fachada frontal (hacia la calle)."""
        # TODO: implementar en Fase 2
        raise NotImplementedError("GeneradorFachada — pendiente Fase 2")
