"""
motor.py
--------
Motor de vista previa geométrica.

Coordina los renderizadores según la sección activa del panel de configuración.
Funciona completamente independiente de Revit; usa pyvista/VTK internamente.

El motor responde a cambios en el Proyecto y delega el renderizado al
renderizador correspondiente a la sección activa (RF-02).
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
    GENERAL       = "general"        # Volumen 3D del edificio
    LOTE          = "lote"           # Vista superior con polígono de lote
    TIPOLOGIAS    = "tipologias"     # Planta interactiva de unidad
    AMBIENTES     = "ambientes"      # Distribución interior del departamento
    CIRCULACION   = "circulacion"    # Planta del piso con núcleos y pasillos
    ESTRUCTURA    = "estructura"     # Grilla estructural con columnas y vigas
    FACHADA       = "fachada"        # Vista 3D frontal del edificio
    MATERIALES    = "materiales"     # Muestras visuales de materiales
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
        # Callback llamado cuando la vista previa está lista (actualiza el widget Qt)
        self.al_cambiar: Optional[Callable] = None

    def actualizar(
        self,
        proyecto: "Proyecto",
        seccion: SeccionActiva,
        contexto: Optional[dict] = None,
    ) -> None:
        """
        Regenera la vista previa para el proyecto y la sección indicada.
        Llama a al_cambiar con la geometría resultante.

        Args:
            proyecto: Proyecto actual.
            seccion:  Sección del panel activo.
            contexto: Diccionario de contexto adicional para el renderizador
                      (p.ej. {"unidad_idx": 1} para RenderizadorUnidad,
                             {"planta_idx": 2} para RenderizadorCirculacion).
        """
        self._proyecto = proyecto
        self._seccion  = seccion

        renderizador = self._obtener_renderizador(seccion)
        if renderizador is None:
            return

        geometria = renderizador.renderizar(proyecto, contexto)
        if self.al_cambiar:
            self.al_cambiar(geometria)

    def _obtener_renderizador(self, seccion: SeccionActiva):
        """Devuelve el renderizador correspondiente a la sección activa."""
        from bim_generador.vista_previa.renderizadores.volumen    import RenderizadorVolumen
        from bim_generador.vista_previa.renderizadores.lote       import RenderizadorLote
        from bim_generador.vista_previa.renderizadores.unidad     import RenderizadorUnidad
        from bim_generador.vista_previa.renderizadores.ambientes  import RenderizadorAmbientes
        from bim_generador.vista_previa.renderizadores.circulacion import RenderizadorCirculacion
        from bim_generador.vista_previa.renderizadores.estructura  import RenderizadorEstructura

        mapa = {
            SeccionActiva.GENERAL:     RenderizadorVolumen(),
            SeccionActiva.LOTE:        RenderizadorLote(),
            SeccionActiva.TIPOLOGIAS:  RenderizadorUnidad(),
            SeccionActiva.AMBIENTES:   RenderizadorAmbientes(),
            SeccionActiva.CIRCULACION: RenderizadorCirculacion(),
            SeccionActiva.ESTRUCTURA:  RenderizadorEstructura(),
        }
        return mapa.get(seccion)
