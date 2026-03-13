"""
panel_lote.py
-------------
Panel de configuración de lote e implantación.
Vista previa: vista superior con polígono de lote y huella del edificio.

Estado: STUB — implementación planificada para Sprint 3-4.
"""
from bim_generador.interfaz.paneles.panel_base import PanelBase
from bim_generador.vista_previa.motor          import SeccionActiva


class PanelLote(PanelBase):
    """Panel: Lote / Implantación."""

    @property
    def seccion(self) -> SeccionActiva:
        return SeccionActiva.LOTE

    def _configurar_ui(self) -> None:
        super()._configurar_ui()
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore    import Qt
        lbl = QLabel("🏗 Panel de Lote / Implantación\n\n(Próximamente — Sprint 3)")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #7EB8F7; font-size: 13px;")
        self.layout().addWidget(lbl)
        self.layout().addStretch()
