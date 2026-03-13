"""
panel_base.py
-------------
Clase base para todos los paneles de configuración.

Cada panel:
  1. Recibe una referencia al Proyecto actual.
  2. Expone un signal `parametros_cambiados` que se emite al modificar cualquier valor.
  3. Implementa `cargar(proyecto)` para poblar la UI con los valores actuales.
  4. Implementa `seccion` (property) que retorna la SeccionActiva correspondiente.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore    import pyqtSignal, Qt

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto
    from bim_generador.vista_previa.motor      import SeccionActiva


class PanelBase(QWidget):
    """
    Panel de configuración base.

    Señales:
        parametros_cambiados: emitida cuando el usuario modifica algún parámetro.
    """

    parametros_cambiados = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._proyecto: Optional["Proyecto"] = None
        self._configurar_ui()

    def _configurar_ui(self) -> None:
        """Construye la UI del panel. Sobreescribir en subclases."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

    @property
    def seccion(self) -> "SeccionActiva":
        """Retorna la sección del preview que activa este panel."""
        from bim_generador.vista_previa.motor import SeccionActiva
        return SeccionActiva.GENERAL  # sobreescribir en subclases

    @property
    def contexto_render(self) -> dict:
        """
        Contexto adicional para el renderizador de vista previa.
        Sobreescribir en paneles que necesiten pasar datos extra
        (p.ej. PanelTipologias pasa {"unidad_idx": N}).
        """
        return {}

    def cargar(self, proyecto: "Proyecto") -> None:
        """Carga los valores del proyecto en los controles del panel."""
        self._proyecto = proyecto

    def _emitir_cambio(self) -> None:
        """Helper: emite la señal de cambio desde cualquier slot de control."""
        self.parametros_cambiados.emit()
