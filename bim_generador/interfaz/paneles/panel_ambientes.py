"""
panel_ambientes.py
------------------
Panel de edición de Ambientes individuales dentro de una unidad funcional.

Secciones:
    - Selección      : selector de unidad (spin) + selector de ambiente (combo)
    - Propiedades    : superficie, ancho mínimo, nombre, iluminación, ventilación
    - Validación     : indicador normativo por ambiente (Cód. Urbano CABA)
    - Métricas       : totales de la unidad seleccionada

Vista previa asociada: RenderizadorAmbientes (planta 2D con ambiente resaltado).
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
    QGroupBox, QWidget, QSpinBox, QFrame, QCheckBox, QLineEdit,
)
from PyQt6.QtCore import Qt

from bim_generador.interfaz.paneles.panel_base import PanelBase
from bim_generador.vista_previa.motor          import SeccionActiva
from bim_generador.nucleo.motor_parametros     import TipoAmbiente, TipoPlanta

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto, Unidad, Ambiente


# Superficies mínimas del Código Urbano CABA (Art. 4.3)
# Fuente: configuracion/normas/argentina_caba.json — min_room_areas
_SUPERFICIES_MINIMAS: dict[TipoAmbiente, float] = {
    TipoAmbiente.DORMITORIO_SIMPLE:    9.0,
    TipoAmbiente.DORMITORIO_PRINCIPAL: 12.0,
    TipoAmbiente.LIVING_COMEDOR:       16.0,
    TipoAmbiente.COCINA:               6.0,
    TipoAmbiente.BANIO:                3.5,
    TipoAmbiente.TOILETTE:             2.0,
    TipoAmbiente.LAVADERO:             2.5,
    TipoAmbiente.ESTUDIO:              6.0,
}

# Anchos mínimos del Código Urbano CABA (min_room_dimensions_m)
_ANCHOS_MINIMOS: dict[TipoAmbiente, float] = {
    TipoAmbiente.DORMITORIO_SIMPLE:    2.50,
    TipoAmbiente.DORMITORIO_PRINCIPAL: 3.00,
    TipoAmbiente.LIVING_COMEDOR:       3.50,
    TipoAmbiente.COCINA:               2.00,
    TipoAmbiente.BANIO:                1.50,
    TipoAmbiente.TOILETTE:             1.20,
    TipoAmbiente.LAVADERO:             1.50,
}

# Ambientes que requieren iluminación y ventilación natural obligatorias
_HABITABLES = frozenset({
    TipoAmbiente.DORMITORIO_SIMPLE,
    TipoAmbiente.DORMITORIO_PRINCIPAL,
    TipoAmbiente.LIVING_COMEDOR,
    TipoAmbiente.ESTUDIO,
})

# Nombres visibles para el combo de ambientes
_NOMBRES_TIPO: dict[TipoAmbiente, str] = {
    TipoAmbiente.DORMITORIO_SIMPLE:    "Dormitorio simple",
    TipoAmbiente.DORMITORIO_PRINCIPAL: "Dormitorio principal",
    TipoAmbiente.LIVING_COMEDOR:       "Living comedor",
    TipoAmbiente.COCINA:               "Cocina",
    TipoAmbiente.BANIO:                "Baño",
    TipoAmbiente.TOILETTE:             "Toilette",
    TipoAmbiente.LAVADERO:             "Lavadero",
    TipoAmbiente.ESTUDIO:              "Estudio",
    TipoAmbiente.BALCON:               "Balcón",
    TipoAmbiente.CIRCULACION_INTERNA:  "Circulación interna",
}


class PanelAmbientes(PanelBase):
    """
    Panel de edición de ambientes individuales dentro de una unidad funcional.

    Permite seleccionar la unidad (por índice) y el ambiente dentro de ella,
    editar sus propiedades y ver la validación normativa en tiempo real.
    La vista previa resalta el ambiente seleccionado en la planta 2D.
    """

    @property
    def seccion(self) -> SeccionActiva:
        return SeccionActiva.AMBIENTES

    @property
    def contexto_render(self) -> dict:
        return {
            "unidad_idx":  self._spin_unidad.value(),
            "ambiente_idx": self._idx_ambiente_actual,
        }

    def _configurar_ui(self) -> None:
        super()._configurar_ui()
        layout: QVBoxLayout = self.layout()

        # Título
        titulo = QLabel("🛋 Ambientes")
        titulo.setStyleSheet("font-size:14px; font-weight:bold; color:#C8D0E0;")
        layout.addWidget(titulo)

        # ---- Grupo selección ------------------------------------------------
        self._crear_grupo_seleccion(layout)

        # ---- Grupo propiedades ----------------------------------------------
        self._crear_grupo_propiedades(layout)

        # ---- Grupo validación normativa -------------------------------------
        self._crear_grupo_validacion(layout)

        # ---- Grupo métricas de unidad ---------------------------------------
        self._crear_grupo_metricas(layout)

        layout.addStretch()

        # Estado interno
        self._idx_ambiente_actual: int = 0
        self._cargando: bool = False  # bandera para evitar disparos al cargar

    # -----------------------------------------------------------------------
    # Construcción de secciones de UI
    # -----------------------------------------------------------------------

    def _crear_grupo_seleccion(self, layout: QVBoxLayout) -> None:
        grp = QGroupBox("Selección")
        form = QVBoxLayout(grp)

        # Selector de unidad
        fila_u = QHBoxLayout()
        lbl_u = QLabel("Unidad:")
        lbl_u.setFixedWidth(70)
        self._spin_unidad = QSpinBox()
        self._spin_unidad.setMinimum(0)
        self._spin_unidad.setMaximum(0)
        self._spin_unidad.setFixedWidth(54)
        self._spin_unidad.valueChanged.connect(self._al_cambiar_unidad)
        self._lbl_tip_unidad = QLabel("—")
        self._lbl_tip_unidad.setStyleSheet("color:#7EB8F7; font-size:11px;")
        fila_u.addWidget(lbl_u)
        fila_u.addWidget(self._spin_unidad)
        fila_u.addWidget(self._lbl_tip_unidad)
        fila_u.addStretch()
        form.addLayout(fila_u)

        # Selector de ambiente
        fila_a = QHBoxLayout()
        lbl_a = QLabel("Ambiente:")
        lbl_a.setFixedWidth(70)
        self._combo_ambiente = QComboBox()
        self._combo_ambiente.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._combo_ambiente.currentIndexChanged.connect(self._al_cambiar_ambiente)
        fila_a.addWidget(lbl_a)
        fila_a.addWidget(self._combo_ambiente)
        fila_a.addStretch()
        form.addLayout(fila_a)

        layout.addWidget(grp)

    def _crear_grupo_propiedades(self, layout: QVBoxLayout) -> None:
        grp = QGroupBox("Propiedades del ambiente")
        form = QVBoxLayout(grp)
        form.setSpacing(6)

        # Nombre custom
        fila_nombre = QHBoxLayout()
        lbl_nombre = QLabel("Nombre:")
        lbl_nombre.setFixedWidth(110)
        self._edit_nombre = QLineEdit()
        self._edit_nombre.setPlaceholderText("(usar tipo por defecto)")
        self._edit_nombre.textChanged.connect(self._al_editar_propiedad)
        fila_nombre.addWidget(lbl_nombre)
        fila_nombre.addWidget(self._edit_nombre)
        form.addLayout(fila_nombre)

        # Superficie
        self._spin_superficie = self._fila_spin(
            form, "Superficie:", "m²", 1.0, 300.0, 0.5, decimals=1
        )
        self._spin_superficie.valueChanged.connect(self._al_editar_propiedad)

        # Ancho mínimo
        self._spin_ancho = self._fila_spin(
            form, "Ancho mínimo:", "m", 0.8, 20.0, 0.1, decimals=2
        )
        self._spin_ancho.valueChanged.connect(self._al_editar_propiedad)

        # Checkboxes de iluminación y ventilación
        self._chk_iluminacion = QCheckBox("Iluminación natural")
        self._chk_ventilacion = QCheckBox("Ventilación natural")
        for chk in (self._chk_iluminacion, self._chk_ventilacion):
            chk.setStyleSheet("color:#C8D0E0; font-size:11px;")
            chk.stateChanged.connect(self._al_editar_propiedad)
        form.addWidget(self._chk_iluminacion)
        form.addWidget(self._chk_ventilacion)

        layout.addWidget(grp)

    def _crear_grupo_validacion(self, layout: QVBoxLayout) -> None:
        grp = QGroupBox("Validación normativa (Cód. Urbano CABA)")
        vbox = QVBoxLayout(grp)
        vbox.setSpacing(4)

        # Superficie mínima
        self._lbl_val_sup_et = QLabel("Superficie mínima: —")
        self._lbl_val_sup_et.setStyleSheet("color:#C8D0E0; font-size:11px;")
        self._ind_sup = self._indicador(vbox, self._lbl_val_sup_et)

        # Ancho mínimo
        self._lbl_val_ancho_et = QLabel("Ancho mínimo: —")
        self._lbl_val_ancho_et.setStyleSheet("color:#C8D0E0; font-size:11px;")
        self._ind_ancho = self._indicador(vbox, self._lbl_val_ancho_et)

        # Habitabilidad
        self._lbl_val_hab = QLabel("—")
        self._lbl_val_hab.setStyleSheet("color:#888; font-size:10px;")
        self._lbl_val_hab.setWordWrap(True)
        vbox.addWidget(self._lbl_val_hab)

        layout.addWidget(grp)

    def _crear_grupo_metricas(self, layout: QVBoxLayout) -> None:
        grp = QGroupBox("Métricas de unidad")
        vbox = QVBoxLayout(grp)

        self._lbl_sup_total   = self._fila_metrica(vbox, "Sup. total:")
        self._lbl_sup_vendible = self._fila_metrica(vbox, "Sup. vendible:")
        self._lbl_dormitorios  = self._fila_metrica(vbox, "Dormitorios:")
        self._lbl_tipologia    = self._fila_metrica(vbox, "Tipología:")

        layout.addWidget(grp)

    # -----------------------------------------------------------------------
    # Helpers de widgets
    # -----------------------------------------------------------------------

    def _fila_spin(
        self,
        layout: QVBoxLayout,
        etiqueta: str,
        sufijo: str,
        minimo: float,
        maximo: float,
        paso: float,
        decimals: int = 1,
    ) -> QDoubleSpinBox:
        fila = QHBoxLayout()
        lbl = QLabel(etiqueta)
        lbl.setFixedWidth(110)
        spin = QDoubleSpinBox()
        spin.setRange(minimo, maximo)
        spin.setSingleStep(paso)
        spin.setDecimals(decimals)
        spin.setSuffix(f" {sufijo}")
        spin.setFixedWidth(100)
        fila.addWidget(lbl)
        fila.addWidget(spin)
        fila.addStretch()
        layout.addLayout(fila)
        return spin

    def _fila_metrica(self, layout: QVBoxLayout, etiqueta: str) -> QLabel:
        fila = QHBoxLayout()
        lbl_et = QLabel(etiqueta)
        lbl_et.setStyleSheet("color:#C8D0E0; font-size:11px;")
        lbl_et.setFixedWidth(100)
        lbl_val = QLabel("—")
        lbl_val.setStyleSheet("color:#7EB8F7; font-weight:bold; font-size:11px;")
        fila.addWidget(lbl_et)
        fila.addWidget(lbl_val)
        fila.addStretch()
        layout.addLayout(fila)
        return lbl_val

    def _indicador(self, layout: QVBoxLayout, lbl_etiqueta: QLabel) -> QLabel:
        fila = QHBoxLayout()
        ind = QLabel("●")
        ind.setFixedWidth(16)
        ind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ind.setStyleSheet("color:#888; font-size:14px;")
        fila.addWidget(ind)
        fila.addWidget(lbl_etiqueta)
        fila.addStretch()
        layout.addLayout(fila)
        return ind

    # -----------------------------------------------------------------------
    # Carga de datos
    # -----------------------------------------------------------------------

    def cargar(self, proyecto: "Proyecto") -> None:
        super().cargar(proyecto)
        self._cargando = True

        # Ajustar rango del spin de unidad
        plantas = proyecto.edificio.plantas
        planta_ref = next(
            (p for p in plantas if p.tipo_planta == TipoPlanta.PLANTA_TIPO),
            plantas[0] if plantas else None,
        ) if plantas else None
        n_unidades = len(planta_ref.unidades) if planta_ref else 0
        self._spin_unidad.setMaximum(max(0, n_unidades - 1))

        self._cargar_ambientes_combo()
        self._cargando = False
        self._cargar_ambiente_actual()
        self._actualizar_metricas()

    def _cargar_ambientes_combo(self) -> None:
        """Puebla el combo de ambientes con los de la unidad seleccionada."""
        self._combo_ambiente.blockSignals(True)
        self._combo_ambiente.clear()

        unidad = self._unidad_actual()
        if unidad:
            for i, amb in enumerate(unidad.ambientes):
                nombre = amb.nombre_custom or _NOMBRES_TIPO.get(amb.tipo, amb.tipo.value)
                self._combo_ambiente.addItem(f"#{i + 1} — {nombre}", i)
            # Actualizar label de tipología
            from bim_generador.interfaz.paneles.panel_tipologias import _NOMBRES_TIPOLOGIA
            self._lbl_tip_unidad.setText(
                _NOMBRES_TIPOLOGIA.get(unidad.tipologia, unidad.tipologia.value)
            )
        self._combo_ambiente.blockSignals(False)

    def _cargar_ambiente_actual(self) -> None:
        """Carga las propiedades del ambiente actual en los controles."""
        amb = self._ambiente_actual()
        if amb is None:
            return

        self._cargando = True
        self._edit_nombre.setText(amb.nombre_custom or "")
        self._spin_superficie.setValue(amb.superficie_m2)
        self._spin_ancho.setValue(amb.ancho_min_m)
        self._chk_iluminacion.setChecked(amb.iluminacion_natural)
        self._chk_ventilacion.setChecked(amb.ventilacion_natural)
        self._cargando = False

        self._actualizar_validacion(amb)
        self._actualizar_metricas()

    # -----------------------------------------------------------------------
    # Slots de cambio
    # -----------------------------------------------------------------------

    def _al_cambiar_unidad(self) -> None:
        if self._cargando or self._proyecto is None:
            return
        self._cargando = True
        self._cargar_ambientes_combo()
        self._idx_ambiente_actual = 0
        self._combo_ambiente.setCurrentIndex(0)
        self._cargando = False
        self._cargar_ambiente_actual()
        self._emitir_cambio()

    def _al_cambiar_ambiente(self, idx: int) -> None:
        if self._cargando or self._proyecto is None:
            return
        self._idx_ambiente_actual = max(0, idx)
        self._cargar_ambiente_actual()
        self._emitir_cambio()

    def _al_editar_propiedad(self) -> None:
        if self._cargando or self._proyecto is None:
            return
        amb = self._ambiente_actual()
        if amb is None:
            return

        # Mutar el ambiente directamente (Pydantic v2 permite mutación)
        nombre = self._edit_nombre.text().strip() or None
        amb.nombre_custom       = nombre
        amb.superficie_m2       = self._spin_superficie.value()
        amb.ancho_min_m         = self._spin_ancho.value()
        amb.iluminacion_natural = self._chk_iluminacion.isChecked()
        amb.ventilacion_natural = self._chk_ventilacion.isChecked()

        # Actualizar el item del combo con el nuevo nombre
        self._combo_ambiente.blockSignals(True)
        nombre_visible = amb.nombre_custom or _NOMBRES_TIPO.get(amb.tipo, amb.tipo.value)
        self._combo_ambiente.setItemText(
            self._combo_ambiente.currentIndex(),
            f"#{self._idx_ambiente_actual + 1} — {nombre_visible}",
        )
        self._combo_ambiente.blockSignals(False)

        self._actualizar_validacion(amb)
        self._actualizar_metricas()
        self._emitir_cambio()

    # -----------------------------------------------------------------------
    # Validación normativa
    # -----------------------------------------------------------------------

    def _actualizar_validacion(self, amb: "Ambiente") -> None:
        """Actualiza los indicadores de cumplimiento normativo del ambiente."""
        # Superficie mínima
        min_sup = _SUPERFICIES_MINIMAS.get(amb.tipo)
        if min_sup is not None:
            self._lbl_val_sup_et.setText(f"Superficie mínima: {min_sup:.1f} m²")
            if amb.superficie_m2 >= min_sup:
                self._ind_sup.setStyleSheet("color:#5BA85F; font-size:14px;")  # verde
            elif amb.superficie_m2 >= min_sup * 0.9:
                self._ind_sup.setStyleSheet("color:#E8A838; font-size:14px;")  # amarillo
            else:
                self._ind_sup.setStyleSheet("color:#D95F5F; font-size:14px;")  # rojo
        else:
            self._lbl_val_sup_et.setText("Superficie mínima: sin requisito")
            self._ind_sup.setStyleSheet("color:#888; font-size:14px;")

        # Ancho mínimo
        min_ancho = _ANCHOS_MINIMOS.get(amb.tipo)
        if min_ancho is not None:
            self._lbl_val_ancho_et.setText(f"Ancho mínimo: {min_ancho:.2f} m")
            if amb.ancho_min_m >= min_ancho:
                self._ind_ancho.setStyleSheet("color:#5BA85F; font-size:14px;")
            else:
                self._ind_ancho.setStyleSheet("color:#D95F5F; font-size:14px;")
        else:
            self._lbl_val_ancho_et.setText("Ancho mínimo: sin requisito")
            self._ind_ancho.setStyleSheet("color:#888; font-size:14px;")

        # Habitabilidad
        if amb.tipo in _HABITABLES:
            faltan = []
            if not amb.iluminacion_natural:
                faltan.append("iluminación natural")
            if not amb.ventilacion_natural:
                faltan.append("ventilación natural")
            if faltan:
                self._lbl_val_hab.setText(
                    f"Ambiente habitable requiere: {', '.join(faltan)}."
                )
                self._lbl_val_hab.setStyleSheet("color:#E8A838; font-size:10px;")
            else:
                self._lbl_val_hab.setText("Habitable: cumple condiciones.")
                self._lbl_val_hab.setStyleSheet("color:#5BA85F; font-size:10px;")
        else:
            self._lbl_val_hab.setText("")

    # -----------------------------------------------------------------------
    # Métricas
    # -----------------------------------------------------------------------

    def _actualizar_metricas(self) -> None:
        unidad = self._unidad_actual()
        if unidad is None:
            return
        self._lbl_sup_total.setText(f"{unidad.superficie_total_m2:.1f} m²")
        self._lbl_sup_vendible.setText(f"{unidad.superficie_vendible_m2:.1f} m²")
        self._lbl_dormitorios.setText(str(unidad.cantidad_dormitorios))
        from bim_generador.interfaz.paneles.panel_tipologias import _NOMBRES_TIPOLOGIA
        self._lbl_tipologia.setText(
            _NOMBRES_TIPOLOGIA.get(unidad.tipologia, unidad.tipologia.value)
        )

    # -----------------------------------------------------------------------
    # Accesores internos
    # -----------------------------------------------------------------------

    def _unidad_actual(self) -> Optional["Unidad"]:
        if self._proyecto is None:
            return None
        plantas = self._proyecto.edificio.plantas
        if not plantas:
            return None
        planta_ref = next(
            (p for p in plantas if p.tipo_planta == TipoPlanta.PLANTA_TIPO),
            plantas[0],
        )
        idx = self._spin_unidad.value()
        if not planta_ref.unidades or idx >= len(planta_ref.unidades):
            return None
        return planta_ref.unidades[idx]

    def _ambiente_actual(self) -> Optional["Ambiente"]:
        unidad = self._unidad_actual()
        if unidad is None or not unidad.ambientes:
            return None
        idx = self._idx_ambiente_actual
        if idx >= len(unidad.ambientes):
            return None
        return unidad.ambientes[idx]
