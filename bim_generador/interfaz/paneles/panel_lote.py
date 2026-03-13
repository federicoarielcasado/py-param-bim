"""
panel_lote.py
-------------
Panel de configuración de Lote e Implantación.

Permite editar las dimensiones del lote, los retiros normativos y los
factores urbanísticos. Muestra métricas calculadas en tiempo real con
un semáforo visual (verde / amarillo / rojo) para FOS y FOT.

Vista previa asociada: RenderizadorLote (vista 2D cenital del lote).
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLabel,
    QDoubleSpinBox, QGroupBox, QFrame,
    QHBoxLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor

from bim_generador.interfaz.paneles.panel_base import PanelBase
from bim_generador.vista_previa.motor          import SeccionActiva

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


# Umbrales del semáforo normativo
_UMBRAL_ADVERTENCIA = 0.90   # > 90 % del máximo → amarillo
_UMBRAL_CRITICO     = 1.00   # > 100 % del máximo → rojo


class _IndicadorNormativo(QFrame):
    """
    Widget pequeño que muestra un valor y un semáforo de colores.

    Verde   → valor ≤ 90 % del límite
    Amarillo → 90 % < valor ≤ 100 % del límite
    Rojo    → valor > 100 % del límite (incumplimiento)
    """

    _ESTILOS = {
        "ok":          "background:#2D7A2D; color:#FFFFFF; border-radius:4px; padding:2px 6px;",
        "advertencia": "background:#B8860B; color:#FFFFFF; border-radius:4px; padding:2px 6px;",
        "critico":     "background:#8B1A1A; color:#FFFFFF; border-radius:4px; padding:2px 6px;",
        "neutro":      "background:#2A2A40; color:#C8D0E0; border-radius:4px; padding:2px 6px;",
    }

    def __init__(self, etiqueta: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        self._lbl_nombre = QLabel(etiqueta)
        self._lbl_nombre.setStyleSheet("color:#C8D0E0; font-size:11px;")
        self._lbl_nombre.setFixedWidth(80)

        self._lbl_valor = QLabel("—")
        self._lbl_valor.setStyleSheet(self._ESTILOS["neutro"])
        self._lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_valor.setFixedWidth(80)

        self._lbl_limite = QLabel("")
        self._lbl_limite.setStyleSheet("color:#7EB8F7; font-size:10px;")

        layout.addWidget(self._lbl_nombre)
        layout.addWidget(self._lbl_valor)
        layout.addWidget(self._lbl_limite)

    def actualizar(self, valor: float, limite: float, unidad: str = "") -> None:
        """Actualiza el valor y recalcula el color del semáforo."""
        if limite <= 0:
            return

        ratio = valor / limite

        if ratio > _UMBRAL_CRITICO:
            estado = "critico"
            icono  = "✗"
        elif ratio > _UMBRAL_ADVERTENCIA:
            estado = "advertencia"
            icono  = "⚠"
        else:
            estado = "ok"
            icono  = "✓"

        self._lbl_valor.setText(f"{icono} {valor:.3f}{unidad}")
        self._lbl_valor.setStyleSheet(self._ESTILOS[estado])
        self._lbl_limite.setText(f"máx {limite:.2f}")

    def limpiar(self) -> None:
        self._lbl_valor.setText("—")
        self._lbl_valor.setStyleSheet(self._ESTILOS["neutro"])
        self._lbl_limite.setText("")


class PanelLote(PanelBase):
    """
    Panel de Lote e Implantación.

    Secciones:
        - Forma del lote    : frente, fondo
        - Retiros           : frontal, lateral, posterior
        - Normativa         : FOS máx, FOT máx, altura máx
        - Métricas calculadas + semáforo de cumplimiento
    """

    @property
    def seccion(self) -> SeccionActiva:
        return SeccionActiva.LOTE

    def _configurar_ui(self) -> None:
        super()._configurar_ui()
        layout: QVBoxLayout = self.layout()

        # ---- Título --------------------------------------------------------
        titulo = QLabel("🏗 Lote e Implantación")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #C8D0E0;")
        layout.addWidget(titulo)

        # ---- Grupo: Forma del lote -----------------------------------------
        grp_forma = QGroupBox("Forma del lote")
        form_forma = QFormLayout(grp_forma)

        self._spin_frente = self._crear_spin(4.0, 200.0, 0.5, " m")
        self._spin_fondo  = self._crear_spin(4.0, 200.0, 0.5, " m")

        form_forma.addRow("Frente:",  self._spin_frente)
        form_forma.addRow("Fondo:",   self._spin_fondo)
        layout.addWidget(grp_forma)

        # ---- Grupo: Retiros ------------------------------------------------
        grp_retiros = QGroupBox("Retiros obligatorios")
        form_retiros = QFormLayout(grp_retiros)

        self._spin_ret_frt  = self._crear_spin(0.0, 30.0, 0.5, " m")
        self._spin_ret_lat  = self._crear_spin(0.0, 30.0, 0.5, " m")
        self._spin_ret_post = self._crear_spin(0.0, 30.0, 0.5, " m")

        form_retiros.addRow("Frontal:",    self._spin_ret_frt)
        form_retiros.addRow("Lateral:",    self._spin_ret_lat)
        form_retiros.addRow("Posterior:",  self._spin_ret_post)
        layout.addWidget(grp_retiros)

        # ---- Grupo: Normativa ----------------------------------------------
        grp_norma = QGroupBox("Normativa (referencia)")
        form_norma = QFormLayout(grp_norma)

        self._spin_fos_max = self._crear_spin(0.1, 1.0, 0.05, "", decimales=2)
        self._spin_fot_max = self._crear_spin(0.1, 15.0, 0.1, "", decimales=1)
        self._spin_alt_max = self._crear_spin(0.0, 200.0, 1.0, " m")
        self._spin_alt_max.setSpecialValueText("Sin límite")

        form_norma.addRow("FOS máx:", self._spin_fos_max)
        form_norma.addRow("FOT máx:", self._spin_fot_max)
        form_norma.addRow("Alt. máx:", self._spin_alt_max)
        layout.addWidget(grp_norma)

        # ---- Grupo: Métricas de implantación -------------------------------
        grp_metricas = QGroupBox("Métricas de implantación")
        layout_metricas = QVBoxLayout(grp_metricas)
        layout_metricas.setSpacing(4)

        # Filas de métricas simples
        self._lbl_sup_lote       = self._crear_fila_metrica(layout_metricas, "Sup. lote:")
        self._lbl_sup_edificable = self._crear_fila_metrica(layout_metricas, "Edificable (FOS):")
        self._lbl_sup_construible = self._crear_fila_metrica(layout_metricas, "Construible (FOT):")
        self._lbl_zona_libre     = self._crear_fila_metrica(layout_metricas, "Zona libre:")

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border: 1px solid #3A3A5C; margin: 4px 0;")
        layout_metricas.addWidget(sep)

        # Indicadores de cumplimiento normativo
        lbl_norma = QLabel("Cumplimiento normativo:")
        lbl_norma.setStyleSheet("color:#7EB8F7; font-size:11px; font-weight:bold;")
        layout_metricas.addWidget(lbl_norma)

        self._ind_fos = _IndicadorNormativo("FOS real:")
        self._ind_fot = _IndicadorNormativo("FOT real:")
        layout_metricas.addWidget(self._ind_fos)
        layout_metricas.addWidget(self._ind_fot)

        layout.addWidget(grp_metricas)
        layout.addStretch()

        # ---- Conectar señales ---------------------------------------------
        for spin in (self._spin_frente, self._spin_fondo,
                     self._spin_ret_frt, self._spin_ret_lat, self._spin_ret_post,
                     self._spin_fos_max, self._spin_fot_max, self._spin_alt_max):
            spin.valueChanged.connect(self._al_cambiar_valor)

    # ---- helpers de UI -----------------------------------------------------

    def _crear_spin(self, minimo: float, maximo: float, paso: float,
                    sufijo: str, decimales: int = 1) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(minimo, maximo)
        sb.setSingleStep(paso)
        sb.setDecimals(decimales)
        sb.setSuffix(sufijo)
        return sb

    def _crear_fila_metrica(self, layout: QVBoxLayout, etiqueta: str) -> QLabel:
        """Agrega una fila etiqueta: valor al layout y retorna el QLabel del valor."""
        fila = QHBoxLayout()
        lbl_et = QLabel(etiqueta)
        lbl_et.setStyleSheet("color:#C8D0E0; font-size:11px;")
        lbl_et.setFixedWidth(120)

        lbl_val = QLabel("—")
        lbl_val.setStyleSheet("color:#7EB8F7; font-weight:bold; font-size:11px;")

        fila.addWidget(lbl_et)
        fila.addWidget(lbl_val)
        fila.addStretch()
        layout.addLayout(fila)
        return lbl_val

    # ---- carga de datos ----------------------------------------------------

    def cargar(self, proyecto: "Proyecto") -> None:
        super().cargar(proyecto)
        self._bloquear_señales(True)

        self._spin_frente.setValue(proyecto.lote.frente_m)
        self._spin_fondo.setValue(proyecto.lote.fondo_m)
        self._spin_ret_frt.setValue(proyecto.edificio.retiro_frontal_m)
        self._spin_ret_lat.setValue(proyecto.edificio.retiro_lateral_m)
        self._spin_ret_post.setValue(proyecto.edificio.retiro_posterior_m)
        self._spin_fos_max.setValue(proyecto.lote.fos_max)
        self._spin_fot_max.setValue(proyecto.lote.fot_max)

        alt_max = proyecto.lote.altura_max_m
        self._spin_alt_max.setValue(alt_max if alt_max is not None else 0.0)

        self._bloquear_señales(False)
        self._actualizar_metricas()

    def _actualizar_metricas(self) -> None:
        if self._proyecto is None:
            return

        p   = self._proyecto
        lote = p.lote
        ed   = p.edificio

        sup_lote        = lote.superficie_m2
        sup_edificable  = lote.superficie_edificable_m2
        sup_construible = lote.superficie_total_construible_m2

        # Área libre = lote - zona edificable interior
        x0, y0 = ed.retiro_lateral_m, ed.retiro_posterior_m
        x1, y1 = lote.frente_m - ed.retiro_lateral_m, lote.fondo_m - ed.retiro_frontal_m
        sup_huella = max(0.0, (x1 - x0) * (y1 - y0))
        sup_libre  = sup_lote - sup_huella
        pct_libre  = (sup_libre / sup_lote * 100) if sup_lote > 0 else 0.0

        self._lbl_sup_lote.setText(f"{sup_lote:.1f} m²")
        self._lbl_sup_edificable.setText(f"{sup_edificable:.1f} m²")
        self._lbl_sup_construible.setText(f"{sup_construible:.1f} m²")
        self._lbl_zona_libre.setText(f"{sup_libre:.1f} m² ({pct_libre:.0f} %)")

        # Semáforos
        fos_real = p.calcular_fos_real()
        fot_real = p.calcular_fot_real()
        self._ind_fos.actualizar(fos_real, lote.fos_max)
        self._ind_fot.actualizar(fot_real, lote.fot_max)

    def _bloquear_señales(self, bloquear: bool) -> None:
        for spin in (self._spin_frente, self._spin_fondo,
                     self._spin_ret_frt, self._spin_ret_lat, self._spin_ret_post,
                     self._spin_fos_max, self._spin_fot_max, self._spin_alt_max):
            spin.blockSignals(bloquear)

    # ---- slot de cambio ----------------------------------------------------

    def _al_cambiar_valor(self) -> None:
        if self._proyecto is None:
            return

        lote = self._proyecto.lote
        ed   = self._proyecto.edificio

        lote.frente_m = self._spin_frente.value()
        lote.fondo_m  = self._spin_fondo.value()
        lote.fos_max  = self._spin_fos_max.value()
        lote.fot_max  = self._spin_fot_max.value()

        alt = self._spin_alt_max.value()
        lote.altura_max_m = alt if alt > 0.0 else None

        ed.retiro_frontal_m   = self._spin_ret_frt.value()
        ed.retiro_lateral_m   = self._spin_ret_lat.value()
        ed.retiro_posterior_m = self._spin_ret_post.value()

        self._actualizar_metricas()
        self._emitir_cambio()
