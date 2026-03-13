"""
motor_reglas.py
---------------
Motor de reglas de diseño arquitectónico.

Aplica restricciones y propagaciones entre niveles de la jerarquía
de parámetros: por ejemplo, si cambia el módulo estructural del edificio,
actualiza las superficies mínimas de unidades.

Estado: STUB — implementación planificada para Sprint 2-3.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class MotorReglas:
    """
    Aplica reglas de diseño sobre un Proyecto y devuelve advertencias.

    Uso previsto:
        motor = MotorReglas()
        advertencias = motor.evaluar(proyecto)
    """

    def evaluar(self, proyecto: "Proyecto") -> list[str]:
        """
        Evalúa todas las reglas sobre el proyecto.

        Retorna:
            Lista de strings con advertencias o errores de diseño.
        """
        # TODO: implementar reglas en Sprint 2
        return []
