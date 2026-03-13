"""
motor.py
--------
Motor de vista previa geométrica.

Coordina los renderizadores según la sección activa del panel de configuración.
Funciona completamente independiente de Revit; usa pyvista/VTK internamente.

El motor responde a cambios en el Proyecto y delega el renderizado al
renderizador correspondiente a la sección activa (RF-02 del Claude.md).

Estado: STUB parcial — implementación de volumen 3D planificada para Sprint 3-4.
"""

from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, Optional, Callable

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class SeccionActiva(str, Enum):
    """
    Sección del panel de configuración actualmente visible.
    Determina qué tipo de vista previa se muestra (RF-02).
    """
    GENERAL      = "general"       # Volumen 3D del edificio
    LOTE         = "lote"          # Vista superior con polígono de lote
    TIPOLOGIAS   = "tipologias"    # Planta interactiva de unidad
    AMBIENTES    = "ambientes"     # Distribución interior del departamento
    CIRCULACION  = "circulacion"   # Planta del piso con núcleos y pasillos
    ESTRUCTURA   = "estructura"    # Grilla estructural con columnas y vigas
    FACHADA      = "fachada"       # Vista 3D frontal del edificio
    MATERIALES   = "materiales"    # Muestras visuales de materiales
    DOCUMENTACION = "documentacion"  # Vista previa de plano simplificado


class MotorVista:
    """
    Coordina la generación de vista previa según la sección activa.

    Uso:
        motor = MotorVista()
        motor.al_cambiar = mi_callback_qt
        motor.actualizar(proyecto, SeccionActiva.GENERAL)
    """

    def __init__(self):
        self._proyecto: Optional["Proyecto"] = None
        self._seccion: SeccionActiva = SeccionActiva.GENERAL
        # Callback llamado cuando la vista previa está lista (para actualizar el widget Qt)
        self.al_cambiar: Optional[Callable] = None

    def actualizar(self, proyecto: "Proyecto", seccion: SeccionActiva) -> None:
        """
        Regenera la vista previa para el proyecto y la sección indicada.
        Llama a al_cambiar con la geometría resultante.
        """
        self._proyecto = proyecto
        self._seccion  = seccion

        renderizador = self._obtener_renderizador(seccion)
        if renderizador is None:
            return

        geometria = renderizador.renderizar(proyecto)
        if self.al_cambiar:
            self.al_cambiar(geometria)

    def _obtener_renderizador(self, seccion: SeccionActiva):
        """Devuelve el renderizador correspondiente a la sección activa."""
        from bim_generador.vista_previa.renderizadores.volumen import RenderizadorVolumen

        mapa = {
            SeccionActiva.GENERAL:   RenderizadorVolumen(),
            # Resto de renderizadores se agregan a medida que se implementan
        }
        return mapa.get(seccion)
