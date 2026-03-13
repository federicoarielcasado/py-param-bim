"""
panel_general.py
----------------
Panel de parámetros generales del proyecto.

Permite editar: nombre del proyecto, datos del lote (frente, fondo, FOS, FOT)
y parámetros globales del edificio (cantidad de pisos, altura libre).

Al modificar cualquier valor, emite `parametros_cambiados` lo que dispara
la regeneración del preview volumétrico 3D.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox,
    QGroupBox, QSizePolicy,
)
from PyQt6.QtCore import Qt

from bim_generador.interfaz.paneles.panel_base import PanelBase
from bim_generador.vista_previa.motor          import SeccionActiva

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class PanelGeneral(PanelBase):
    """
    Panel de configuración: parámetros generales.

    Secciones:
        - Proyecto    : nombre
        - Lote        : frente, fondo, FOS máx, FOT máx
        - Edificio    : cantidad de pisos, altura libre por piso, retiros
    """

    @property
    def seccion(self) -> SeccionActiva:
        return SeccionActiva.GENERAL

    def _configurar_ui(self) -> None:
        super()._configurar_ui()
        layout: QVBoxLayout = self.layout()

        # ---- Título --------------------------------------------------------
        titulo = QLabel("⚙ Parámetros Generales")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #C8D0E0;")
        layout.addWidget(titulo)

        # ---- Grupo: Proyecto -----------------------------------------------
        grp_proyecto = QGroupBox("Proyecto")
        form_proyecto = QFormLayout(grp_proyecto)
        self._inp_nombre = QLineEdit()
        self._inp_nombre.setPlaceholderText("Nombre del proyecto")
        form_proyecto.addRow("Nombre:", self._inp_nombre)
        layout.addWidget(grp_proyecto)

        # ---- Grupo: Lote ---------------------------------------------------
        grp_lote = QGroupBox("Lote")
        form_lote = QFormLayout(grp_lote)

        self._spin_frente = self._crear_selector(4.0, 200.0, 1.0, " m")
        self._spin_fondo  = self._crear_selector(4.0, 200.0, 1.0, " m")
        self._spin_fos    = self._crear_selector(0.1, 1.0,   0.05, "", decimales=2)
        self._spin_fot    = self._crear_selector(0.1, 15.0,  0.1,  "", decimales=1)

        form_lote.addRow("Frente:",   self._spin_frente)
        form_lote.addRow("Fondo:",    self._spin_fondo)
        form_lote.addRow("FOS máx:", self._spin_fos)
        form_lote.addRow("FOT máx:", self._spin_fot)
        layout.addWidget(grp_lote)

        # ---- Grupo: Edificio -----------------------------------------------
        grp_edificio = QGroupBox("Edificio")
        form_edificio = QFormLayout(grp_edificio)

        self._spin_pisos    = QSpinBox()
        self._spin_pisos.setRange(1, 50)
        self._spin_pisos.setSuffix(" pisos")

        self._spin_altura   = self._crear_selector(2.4, 4.5, 0.05, " m")
        self._spin_ret_frt  = self._crear_selector(0.0, 20.0, 0.5, " m")
        self._spin_ret_lat  = self._crear_selector(0.0, 20.0, 0.5, " m")
        self._spin_ret_post = self._crear_selector(0.0, 20.0, 0.5, " m")

        form_edificio.addRow("Cantidad de pisos:", self._spin_pisos)
        form_edificio.addRow("Altura libre/piso:", self._spin_altura)
        form_edificio.addRow("Retiro frontal:",    self._spin_ret_frt)
        form_edificio.addRow("Retiro lateral:",    self._spin_ret_lat)
        form_edificio.addRow("Retiro posterior:",  self._spin_ret_post)
        layout.addWidget(grp_edificio)

        # ---- Métricas calculadas (solo lectura) ----------------------------
        grp_metricas = QGroupBox("Métricas del Proyecto")
        form_metricas = QFormLayout(grp_metricas)

        self._lbl_sup_lote    = QLabel("—")
        self._lbl_fos_real    = QLabel("—")
        self._lbl_fot_real    = QLabel("—")
        self._lbl_altura_tot  = QLabel("—")
        self._lbl_total_unid  = QLabel("—")

        for lbl in (self._lbl_sup_lote, self._lbl_fos_real, self._lbl_fot_real,
                    self._lbl_altura_tot, self._lbl_total_unid):
            lbl.setStyleSheet("color: #7EB8F7; font-weight: bold;")

        form_metricas.addRow("Sup. lote:",      self._lbl_sup_lote)
        form_metricas.addRow("FOS real:",        self._lbl_fos_real)
        form_metricas.addRow("FOT real:",        self._lbl_fot_real)
        form_metricas.addRow("Altura total:",    self._lbl_altura_tot)
        form_metricas.addRow("Total unidades:",  self._lbl_total_unid)
        layout.addWidget(grp_metricas)

        layout.addStretch()

        # ---- Conectar señales ---------------------------------------------
        self._inp_nombre.textChanged.connect(self._al_cambiar_nombre)
        self._spin_frente.valueChanged.connect(self._al_cambiar_lote)
        self._spin_fondo.valueChanged.connect(self._al_cambiar_lote)
        self._spin_fos.valueChanged.connect(self._al_cambiar_lote)
        self._spin_fot.valueChanged.connect(self._al_cambiar_lote)
        self._spin_pisos.valueChanged.connect(self._al_cambiar_edificio)
        self._spin_altura.valueChanged.connect(self._al_cambiar_edificio)
        self._spin_ret_frt.valueChanged.connect(self._al_cambiar_edificio)
        self._spin_ret_lat.valueChanged.connect(self._al_cambiar_edificio)
        self._spin_ret_post.valueChanged.connect(self._al_cambiar_edificio)

    # ---- helpers de UI -----------------------------------------------------

    def _crear_selector(self, minimo: float, maximo: float, paso: float,
                        sufijo: str, decimales: int = 2) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(minimo, maximo)
        sb.setSingleStep(paso)
        sb.setDecimals(decimales)
        sb.setSuffix(sufijo)
        return sb

    # ---- carga de datos ----------------------------------------------------

    def cargar(self, proyecto: "Proyecto") -> None:
        super().cargar(proyecto)
        self._bloquear_señales(True)

        self._inp_nombre.setText(proyecto.nombre)
        self._spin_frente.setValue(proyecto.lote.frente_m)
        self._spin_fondo.setValue(proyecto.lote.fondo_m)
        self._spin_fos.setValue(proyecto.lote.fos_max)
        self._spin_fot.setValue(proyecto.lote.fot_max)
        self._spin_pisos.setValue(proyecto.edificio.cantidad_pisos)

        # Altura libre de la primera planta tipo como referencia
        altura_ref = 2.65
        for p in proyecto.edificio.plantas:
            altura_ref = p.altura_libre_m
            break
        self._spin_altura.setValue(altura_ref)
        self._spin_ret_frt.setValue(proyecto.edificio.retiro_frontal_m)
        self._spin_ret_lat.setValue(proyecto.edificio.retiro_lateral_m)
        self._spin_ret_post.setValue(proyecto.edificio.retiro_posterior_m)

        self._bloquear_señales(False)
        self._actualizar_metricas()

    def _actualizar_metricas(self) -> None:
        if self._proyecto is None:
            return
        p = self._proyecto
        self._lbl_sup_lote.setText(f"{p.lote.superficie_m2:.1f} m²")
        self._lbl_fos_real.setText(f"{p.calcular_fos_real():.3f}")
        self._lbl_fot_real.setText(f"{p.calcular_fot_real():.3f}")
        self._lbl_altura_tot.setText(f"{p.edificio.altura_total_m:.2f} m")
        self._lbl_total_unid.setText(str(p.edificio.total_unidades))

    def _bloquear_señales(self, bloquear: bool) -> None:
        for widget in (self._spin_frente, self._spin_fondo, self._spin_fos,
                       self._spin_fot, self._spin_pisos, self._spin_altura,
                       self._spin_ret_frt, self._spin_ret_lat, self._spin_ret_post,
                       self._inp_nombre):
            widget.blockSignals(bloquear)

    # ---- slots de cambio ---------------------------------------------------

    def _al_cambiar_nombre(self, texto: str) -> None:
        if self._proyecto:
            self._proyecto.nombre = texto
            self._proyecto.edificio.nombre = texto
        self._emitir_cambio()

    def _al_cambiar_lote(self) -> None:
        if self._proyecto:
            self._proyecto.lote.frente_m = self._spin_frente.value()
            self._proyecto.lote.fondo_m  = self._spin_fondo.value()
            self._proyecto.lote.fos_max  = self._spin_fos.value()
            self._proyecto.lote.fot_max  = self._spin_fot.value()
        self._actualizar_metricas()
        self._emitir_cambio()

    def _al_cambiar_edificio(self) -> None:
        if self._proyecto:
            ed = self._proyecto.edificio
            nueva_cantidad = self._spin_pisos.value()
            if nueva_cantidad != ed.cantidad_pisos:
                ed.cantidad_pisos = nueva_cantidad
                # Regenerar plantas con la nueva cantidad de pisos
                unidades_tipo = ed.plantas[0].unidades if ed.plantas else []
                ed.generar_plantas_tipo(unidades_tipo)

            ed.retiro_frontal_m   = self._spin_ret_frt.value()
            ed.retiro_lateral_m   = self._spin_ret_lat.value()
            ed.retiro_posterior_m = self._spin_ret_post.value()

            # Actualizar altura de todas las plantas
            nueva_altura = self._spin_altura.value()
            for planta in ed.plantas:
                planta.altura_libre_m = nueva_altura

        self._actualizar_metricas()
        self._emitir_cambio()
