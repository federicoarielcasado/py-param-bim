"""
panel_circulacion.py
--------------------
Panel de Circulación y Distribución en Planta.

Permite seleccionar el piso a visualizar y muestra métricas de circulación
calculadas automáticamente a partir de la geometría de planta:
    - Distancia máxima de evacuación al núcleo
    - Ancho de pasillo
    - Ratio de circulación (pasillo + núcleo / superficie total de planta)
    - Número de unidades en la planta seleccionada

Vista previa asociada: RenderizadorCirculacion (planta 2D con unidades y circulación).
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QGroupBox, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt

from bim_generador.interfaz.paneles.panel_base import PanelBase
from bim_generador.vista_previa.motor          import SeccionActiva

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


# Umbral normativo para distancia de evacuación (CIRSOC / código urbano)
_MAX_EVAC_M = 40.0


class PanelCirculacion(PanelBase):
    """
    Panel de Circulación y Distribución en Planta.

    Secciones:
        - Selector de piso       : elige qué planta visualizar
        - Métricas de circulación: distancia evacuación, ancho pasillo, ratio
    """

    @property
    def seccion(self) -> SeccionActiva:
        return SeccionActiva.CIRCULACION

    @property
    def contexto_render(self) -> dict:
        """Pasa al RenderizadorCirculacion el índice de planta seleccionado."""
        return {"planta_idx": self._combo_planta.currentIndex()}

    def _configurar_ui(self) -> None:
        super()._configurar_ui()
        layout: QVBoxLayout = self.layout()

        # ---- Título ---------------------------------------------------------
        titulo = QLabel("🏢 Circulación y Planta")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #C8D0E0;")
        layout.addWidget(titulo)

        # ---- Grupo: selector de piso ----------------------------------------
        grp_piso = QGroupBox("Piso a visualizar")
        layout_piso = QVBoxLayout(grp_piso)

        self._combo_planta = QComboBox()
        self._combo_planta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo_planta.currentIndexChanged.connect(self._al_cambiar_planta)
        layout_piso.addWidget(self._combo_planta)

        layout.addWidget(grp_piso)

        # ---- Grupo: métricas de circulación ---------------------------------
        grp_met = QGroupBox("Métricas de circulación")
        layout_met = QVBoxLayout(grp_met)
        layout_met.setSpacing(4)

        self._lbl_dist_evac    = self._fila_metrica(layout_met, "Dist. evacuación:")
        self._lbl_ancho_pasillo = self._fila_metrica(layout_met, "Ancho pasillo:")
        self._lbl_ratio_circ   = self._fila_metrica(layout_met, "Ratio circulación:")

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border: 1px solid #3A3A5C; margin: 4px 0;")
        layout_met.addWidget(sep)

        self._lbl_cant_unidades  = self._fila_metrica(layout_met, "Unidades:")
        self._lbl_sup_pasillo    = self._fila_metrica(layout_met, "Sup. pasillo:")
        self._lbl_sup_core       = self._fila_metrica(layout_met, "Sup. núcleo:")

        layout.addWidget(grp_met)

        # ---- Indicador normativo de evacuación ------------------------------
        grp_norma = QGroupBox("Normativa (evacuación)")
        layout_norma = QVBoxLayout(grp_norma)
        layout_norma.setSpacing(4)

        self._ind_evac = _IndicadorEvacuacion()
        layout_norma.addWidget(self._ind_evac)

        layout.addWidget(grp_norma)
        layout.addStretch()

    # ---- helpers de UI ------------------------------------------------------

    def _fila_metrica(self, layout: QVBoxLayout, etiqueta: str) -> QLabel:
        fila    = QHBoxLayout()
        lbl_et  = QLabel(etiqueta)
        lbl_et.setStyleSheet("color:#C8D0E0; font-size:11px;")
        lbl_et.setFixedWidth(130)
        lbl_val = QLabel("—")
        lbl_val.setStyleSheet("color:#7EB8F7; font-weight:bold; font-size:11px;")
        fila.addWidget(lbl_et)
        fila.addWidget(lbl_val)
        fila.addStretch()
        layout.addLayout(fila)
        return lbl_val

    # ---- carga de datos -----------------------------------------------------

    def cargar(self, proyecto: "Proyecto") -> None:
        super().cargar(proyecto)
        self._reconstruir_combo(proyecto)
        self._actualizar_metricas()

    def _reconstruir_combo(self, proyecto: "Proyecto") -> None:
        self._combo_planta.blockSignals(True)
        self._combo_planta.clear()
        for planta in proyecto.edificio.plantas:
            self._combo_planta.addItem(planta.nombre)
        self._combo_planta.blockSignals(False)

    # ---- slot de cambio de planta -------------------------------------------

    def _al_cambiar_planta(self) -> None:
        self._actualizar_metricas()
        self._emitir_cambio()

    # ---- métricas -----------------------------------------------------------

    def _actualizar_metricas(self) -> None:
        if self._proyecto is None:
            return

        plantas = self._proyecto.edificio.plantas
        if not plantas:
            return

        idx    = self._combo_planta.currentIndex()
        idx    = max(0, min(idx, len(plantas) - 1))
        planta = plantas[idx]

        # Calcular geometría de la planta
        from bim_generador.generadores.planta       import GeneradorPlanta
        from bim_generador.generadores.circulacion  import GeneradorCirculacion

        gen_planta = GeneradorPlanta()
        gen_circ   = GeneradorCirculacion()

        geom    = gen_planta.generar(planta, self._proyecto.lote, self._proyecto.edificio)
        metrics = gen_circ.metricas_planta(geom)

        self._lbl_dist_evac.setText(f"{metrics['dist_max_evacuacion_m']:.1f} m")
        self._lbl_ancho_pasillo.setText(f"{metrics['ancho_pasillo_m']:.2f} m")
        self._lbl_ratio_circ.setText(f"{metrics['ratio_circulacion'] * 100:.1f} %")
        self._lbl_cant_unidades.setText(f"{metrics['cantidad_unidades']} unid.")
        self._lbl_sup_pasillo.setText(f"{metrics['sup_pasillo_m2']:.1f} m²")
        self._lbl_sup_core.setText(f"{metrics['sup_core_m2']:.1f} m²")

        self._ind_evac.actualizar(
            metrics["dist_max_evacuacion_m"],
            _MAX_EVAC_M,
        )


# ---------------------------------------------------------------------------
# Widget indicador normativo de evacuación
# ---------------------------------------------------------------------------

class _IndicadorEvacuacion(QFrame):
    """Indicador semáforo para distancia máxima de evacuación."""

    _ESTILOS = {
        "ok":          "background:#2D7A2D; color:#FFFFFF; border-radius:4px; padding:3px 8px;",
        "advertencia": "background:#B8860B; color:#FFFFFF; border-radius:4px; padding:3px 8px;",
        "critico":     "background:#8B1A1A; color:#FFFFFF; border-radius:4px; padding:3px 8px;",
        "neutro":      "background:#2A2A40; color:#C8D0E0; border-radius:4px; padding:3px 8px;",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        lbl_et = QLabel("Dist. evac.:")
        lbl_et.setStyleSheet("color:#C8D0E0; font-size:11px;")
        lbl_et.setFixedWidth(80)

        self._lbl_valor = QLabel("—")
        self._lbl_valor.setStyleSheet(self._ESTILOS["neutro"])
        self._lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_valor.setFixedWidth(90)

        self._lbl_limite = QLabel(f"máx {_MAX_EVAC_M:.0f} m")
        self._lbl_limite.setStyleSheet("color:#7EB8F7; font-size:10px;")

        layout.addWidget(lbl_et)
        layout.addWidget(self._lbl_valor)
        layout.addWidget(self._lbl_limite)

    def actualizar(self, valor: float, limite: float) -> None:
        ratio = valor / limite if limite > 0 else 0.0
        if ratio > 1.0:
            estado, icono = "critico", "✗"
        elif ratio > 0.85:
            estado, icono = "advertencia", "⚠"
        else:
            estado, icono = "ok", "✓"
        self._lbl_valor.setText(f"{icono} {valor:.1f} m")
        self._lbl_valor.setStyleSheet(self._ESTILOS[estado])
