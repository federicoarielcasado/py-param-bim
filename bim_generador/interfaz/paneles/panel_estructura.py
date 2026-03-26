"""
panel_estructura.py
-------------------
Panel de configuración de la estructura portante del edificio.

Permite editar los parámetros de la grilla estructural:
    - Sistema estructural (hormigón armado / metálica / mixta)
    - Módulos de grilla en X e Y
    - Sección de columnas
    - Espesores de losa y muros

Muestra métricas calculadas: cantidad de columnas, área de losa,
volumen estimado de columnas por piso.

Vista previa asociada: RenderizadorEstructura (grilla 2D con columnas y vigas).
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QDoubleSpinBox, QComboBox, QGroupBox, QFrame, QSizePolicy,
)

from bim_generador.interfaz.paneles.panel_base import PanelBase
from bim_generador.vista_previa.motor          import SeccionActiva
from bim_generador.nucleo.motor_parametros     import TipoEstructura

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


_NOMBRES_ESTRUCTURA: dict[TipoEstructura, str] = {
    TipoEstructura.HORMIGON_ARMADO: "Hormigón armado",
    TipoEstructura.METALICA:        "Metálica",
    TipoEstructura.MIXTA:           "Mixta",
}
_ORDEN_ESTRUCTURA = [
    TipoEstructura.HORMIGON_ARMADO,
    TipoEstructura.METALICA,
    TipoEstructura.MIXTA,
]


class PanelEstructura(PanelBase):
    """
    Panel de configuración estructural.

    Secciones:
        - Sistema estructural : tipo (combo)
        - Grilla              : módulos X e Y, sección de columna
        - Espesores           : losa, muro exterior, muro interior
        - Métricas calculadas : columnas, área de losa, volumen estimado
    """

    @property
    def seccion(self) -> SeccionActiva:
        return SeccionActiva.ESTRUCTURA

    def _configurar_ui(self) -> None:
        super()._configurar_ui()
        layout: QVBoxLayout = self.layout()

        # ---- Título ---------------------------------------------------------
        titulo = QLabel("🏗 Estructura")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #C8D0E0;")
        layout.addWidget(titulo)

        # ---- Grupo: sistema estructural -------------------------------------
        grp_tipo = QGroupBox("Sistema estructural")
        form_tipo = QFormLayout(grp_tipo)

        self._combo_tipo = QComboBox()
        for tip in _ORDEN_ESTRUCTURA:
            self._combo_tipo.addItem(_NOMBRES_ESTRUCTURA[tip], tip)
        self._combo_tipo.currentIndexChanged.connect(self._al_cambiar_valor)
        form_tipo.addRow("Tipo:", self._combo_tipo)
        layout.addWidget(grp_tipo)

        # ---- Grupo: grilla --------------------------------------------------
        grp_grilla = QGroupBox("Módulo de grilla")
        form_grilla = QFormLayout(grp_grilla)

        self._spin_mod_x = self._crear_spin(3.0, 9.0, 0.25, " m")
        self._spin_mod_y = self._crear_spin(3.0, 9.0, 0.25, " m")
        self._spin_col   = self._crear_spin(0.20, 0.80, 0.05, " m", decimales=2)

        form_grilla.addRow("Módulo X:",        self._spin_mod_x)
        form_grilla.addRow("Módulo Y:",        self._spin_mod_y)
        form_grilla.addRow("Sección columna:", self._spin_col)
        layout.addWidget(grp_grilla)

        # ---- Grupo: espesores -----------------------------------------------
        grp_esp = QGroupBox("Espesores")
        form_esp = QFormLayout(grp_esp)

        self._spin_losa     = self._crear_spin(0.12, 0.40, 0.02, " m", decimales=2)
        self._spin_muro_ext = self._crear_spin(0.10, 0.40, 0.02, " m", decimales=2)
        self._spin_muro_int = self._crear_spin(0.08, 0.30, 0.01, " m", decimales=2)

        form_esp.addRow("Losa:",          self._spin_losa)
        form_esp.addRow("Muro exterior:", self._spin_muro_ext)
        form_esp.addRow("Muro interior:", self._spin_muro_int)
        layout.addWidget(grp_esp)

        # ---- Grupo: métricas ------------------------------------------------
        grp_met = QGroupBox("Métricas estructurales")
        layout_met = QVBoxLayout(grp_met)
        layout_met.setSpacing(4)

        self._lbl_cant_columnas = self._fila_metrica(layout_met, "Columnas/planta:")
        self._lbl_area_losa     = self._fila_metrica(layout_met, "Área de losa:")
        self._lbl_vol_columnas  = self._fila_metrica(layout_met, "Vol. columnas/piso:")

        layout.addWidget(grp_met)
        layout.addStretch()

        # ---- Conectar señales -----------------------------------------------
        for spin in (self._spin_mod_x, self._spin_mod_y, self._spin_col,
                     self._spin_losa, self._spin_muro_ext, self._spin_muro_int):
            spin.valueChanged.connect(self._al_cambiar_valor)

    # ---- helpers de UI ------------------------------------------------------

    def _crear_spin(
        self,
        minimo: float,
        maximo: float,
        paso: float,
        sufijo: str,
        decimales: int = 1,
    ) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(minimo, maximo)
        sb.setSingleStep(paso)
        sb.setDecimals(decimales)
        sb.setSuffix(sufijo)
        return sb

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
        est = proyecto.edificio.estructura

        self._bloquear_señales(True)

        idx_tipo = _ORDEN_ESTRUCTURA.index(est.tipo_estructura) \
            if est.tipo_estructura in _ORDEN_ESTRUCTURA else 0
        self._combo_tipo.setCurrentIndex(idx_tipo)

        self._spin_mod_x.setValue(est.modulo_x_m)
        self._spin_mod_y.setValue(est.modulo_y_m)
        self._spin_col.setValue(est.seccion_columna_m)
        self._spin_losa.setValue(est.espesor_losa_m)
        self._spin_muro_ext.setValue(est.espesor_muro_ext_m)
        self._spin_muro_int.setValue(est.espesor_muro_int_m)

        self._bloquear_señales(False)
        self._actualizar_metricas()

    # ---- slot de cambio -----------------------------------------------------

    def _al_cambiar_valor(self) -> None:
        if self._proyecto is None:
            return

        est = self._proyecto.edificio.estructura
        est.tipo_estructura     = self._combo_tipo.currentData()
        est.modulo_x_m          = self._spin_mod_x.value()
        est.modulo_y_m          = self._spin_mod_y.value()
        est.seccion_columna_m   = self._spin_col.value()
        est.espesor_losa_m      = self._spin_losa.value()
        est.espesor_muro_ext_m  = self._spin_muro_ext.value()
        est.espesor_muro_int_m  = self._spin_muro_int.value()

        self._actualizar_metricas()
        self._emitir_cambio()

    # ---- métricas -----------------------------------------------------------

    def _actualizar_metricas(self) -> None:
        if self._proyecto is None:
            return

        ed  = self._proyecto.edificio
        est = ed.estructura

        W = max(self._proyecto.lote.frente_m - 2.0 * ed.retiro_lateral_m, 5.0)
        D = max(
            self._proyecto.lote.fondo_m - ed.retiro_frontal_m - ed.retiro_posterior_m,
            8.0,
        )

        mx    = est.modulo_x_m
        my    = est.modulo_y_m
        n_x   = int(W / mx) + 1
        n_y   = int(D / my) + 1
        cant  = n_x * n_y

        sc          = est.seccion_columna_m
        area_losa   = W * D
        altura_piso = 2.65 + est.espesor_losa_m
        vol_cols    = cant * (sc ** 2) * altura_piso

        self._lbl_cant_columnas.setText(f"{cant} col.")
        self._lbl_area_losa.setText(f"{area_losa:.1f} m²")
        self._lbl_vol_columnas.setText(f"{vol_cols:.2f} m³")

    # ---- helpers ------------------------------------------------------------

    def _bloquear_señales(self, bloquear: bool) -> None:
        self._combo_tipo.blockSignals(bloquear)
        for spin in (self._spin_mod_x, self._spin_mod_y, self._spin_col,
                     self._spin_losa, self._spin_muro_ext, self._spin_muro_int):
            spin.blockSignals(bloquear)
