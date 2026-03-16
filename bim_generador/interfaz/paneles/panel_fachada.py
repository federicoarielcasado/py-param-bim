"""
panel_fachada.py — Panel stub. Ver requisitos §3 RF-02.
Estado: STUB — implementación planificada para Fase 2.
"""
from bim_generador.interfaz.paneles.panel_base import PanelBase
from bim_generador.vista_previa.motor import SeccionActiva
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt


class PanelFachada(PanelBase):
    def _configurar_ui(self):
        super()._configurar_ui()
        lbl = QLabel("Panel Fachada\n\n(Próximamente — Fase 2)")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #7EB8F7; font-size: 13px;")
        self.layout().addWidget(lbl)
        self.layout().addStretch()
