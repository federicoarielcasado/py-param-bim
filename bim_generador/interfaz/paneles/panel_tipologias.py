"""
panel_tipologias.py
-------------------
Panel de configuración de Tipologías de Unidades.

Permite editar el mix de unidades funcionales de la planta tipo del edificio.
Los cambios se propagan automáticamente a todas las plantas vía
Edificio.generar_plantas_tipo().

Secciones:
    - Mix de unidades   : lista editable con tipología por unidad (combo + quitar)
    - Vista previa      : selector de unidad a previsualizar en la vista 2D
    - Métricas de planta: totales calculados en tiempo real

Vista previa asociada: RenderizadorUnidad (planta esquemática 2D de departamento).
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QScrollArea, QWidget, QSpinBox, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt

from bim_generador.interfaz.paneles.panel_base    import PanelBase
from bim_generador.vista_previa.motor             import SeccionActiva
from bim_generador.nucleo.motor_parametros        import TipoUnidad, Unidad

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


# Nombres visibles para cada tipología
_NOMBRES_TIPOLOGIA: dict[TipoUnidad, str] = {
    TipoUnidad.MONOAMBIENTE:     "Monoambiente",
    TipoUnidad.DOS_AMBIENTES:    "2 ambientes",
    TipoUnidad.TRES_AMBIENTES:   "3 ambientes",
    TipoUnidad.CUATRO_AMBIENTES: "4 ambientes",
    TipoUnidad.DUPLEX:           "Dúplex",
}

# Orden de visualización en el combo
_ORDEN_TIPOLOGIAS = [
    TipoUnidad.MONOAMBIENTE,
    TipoUnidad.DOS_AMBIENTES,
    TipoUnidad.TRES_AMBIENTES,
    TipoUnidad.CUATRO_AMBIENTES,
    TipoUnidad.DUPLEX,
]


class _FilaUnidad(QFrame):
    """
    Fila individual del mix de unidades.

    Contiene:
        - Número de unidad (label)
        - QComboBox con la tipología seleccionada
        - Botón "×" para eliminar la unidad
    """

    def __init__(self, numero: int, tipologia: TipoUnidad, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._setup(numero, tipologia)

    def _setup(self, numero: int, tipologia: TipoUnidad) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel(f"#{numero}:")
        lbl.setFixedWidth(28)
        lbl.setStyleSheet("color: #7EB8F7; font-size: 11px;")

        self.combo = QComboBox()
        for tip in _ORDEN_TIPOLOGIAS:
            self.combo.addItem(_NOMBRES_TIPOLOGIA[tip], tip)
        # Seleccionar el índice correspondiente a la tipología
        idx = _ORDEN_TIPOLOGIAS.index(tipologia) if tipologia in _ORDEN_TIPOLOGIAS else 0
        self.combo.setCurrentIndex(idx)
        self.combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.btn_quitar = QPushButton("×")
        self.btn_quitar.setFixedWidth(24)
        self.btn_quitar.setFixedHeight(24)
        self.btn_quitar.setStyleSheet(
            "QPushButton { color:#E87070; border:none; font-size:14px; background:transparent; }"
            "QPushButton:hover { color:#FF5050; }"
        )

        layout.addWidget(lbl)
        layout.addWidget(self.combo)
        layout.addWidget(self.btn_quitar)

    def tipologia_seleccionada(self) -> TipoUnidad:
        return self.combo.currentData()


class PanelTipologias(PanelBase):
    """
    Panel de Tipologías de Unidades.

    Edita el mix de departamentos de la planta tipo y muestra métricas
    calculadas en tiempo real. La vista previa 2D muestra el esquema
    de la unidad seleccionada en el spinner "previsualizar".
    """

    @property
    def seccion(self) -> SeccionActiva:
        return SeccionActiva.TIPOLOGIAS

    @property
    def contexto_render(self) -> dict:
        """Pasa al RenderizadorUnidad el índice de unidad a previsualizar."""
        return {"unidad_idx": self._spin_preview.value()}

    def _configurar_ui(self) -> None:
        super()._configurar_ui()
        layout: QVBoxLayout = self.layout()

        # ---- Título ---------------------------------------------------------
        titulo = QLabel("🏠 Tipologías de Unidades")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #C8D0E0;")
        layout.addWidget(titulo)

        # ---- Grupo: mix de unidades -----------------------------------------
        self._grp_mix = QGroupBox("Mix de unidades por planta tipo")
        grp_layout = QVBoxLayout(self._grp_mix)
        grp_layout.setSpacing(4)

        # Área de scroll para la lista dinámica de filas
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setMaximumHeight(180)
        self._scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #2A2A40; background: #13131F; }"
        )

        self._contenedor_filas = QWidget()
        self._layout_filas = QVBoxLayout(self._contenedor_filas)
        self._layout_filas.setSpacing(3)
        self._layout_filas.setContentsMargins(4, 4, 4, 4)
        self._layout_filas.addStretch()   # push rows to top
        self._scroll.setWidget(self._contenedor_filas)
        grp_layout.addWidget(self._scroll)

        # Botón agregar
        self._btn_agregar = QPushButton("+ Agregar unidad")
        self._btn_agregar.setStyleSheet(
            "QPushButton { color:#5BA85F; border:1px solid #3A5C3A; "
            "border-radius:3px; padding:4px 8px; font-size:11px; background:#1A2A1A; }"
            "QPushButton:hover { background:#243A24; }"
        )
        self._btn_agregar.clicked.connect(self._agregar_unidad)
        grp_layout.addWidget(self._btn_agregar)
        layout.addWidget(self._grp_mix)

        # ---- Grupo: vista previa de unidad ----------------------------------
        grp_preview = QGroupBox("Vista previa de unidad")
        form_preview = QHBoxLayout(grp_preview)
        form_preview.setSpacing(8)

        lbl_prev = QLabel("Previsualizar unidad #:")
        lbl_prev.setStyleSheet("color:#C8D0E0; font-size:11px;")

        self._spin_preview = QSpinBox()
        self._spin_preview.setMinimum(0)
        self._spin_preview.setMaximum(0)   # se actualiza dinámicamente
        self._spin_preview.setFixedWidth(54)
        self._spin_preview.valueChanged.connect(self._al_cambiar_preview)

        self._lbl_preview_info = QLabel("—")
        self._lbl_preview_info.setStyleSheet("color:#7EB8F7; font-size:11px;")

        form_preview.addWidget(lbl_prev)
        form_preview.addWidget(self._spin_preview)
        form_preview.addWidget(self._lbl_preview_info)
        form_preview.addStretch()
        layout.addWidget(grp_preview)

        # ---- Grupo: métricas de planta tipo ---------------------------------
        grp_met = QGroupBox("Métricas de planta tipo")
        layout_met = QVBoxLayout(grp_met)
        layout_met.setSpacing(4)

        self._lbl_cantidad_unidades  = self._fila_metrica(layout_met, "Unidades por planta:")
        self._lbl_sup_promedio       = self._fila_metrica(layout_met, "Sup. promedio:")
        self._lbl_sup_total          = self._fila_metrica(layout_met, "Sup. total planta:")

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border: 1px solid #3A3A5C; margin: 4px 0;")
        layout_met.addWidget(sep)

        lbl_desglose = QLabel("Desglose por tipología:")
        lbl_desglose.setStyleSheet("color:#7EB8F7; font-size:11px; font-weight:bold;")
        layout_met.addWidget(lbl_desglose)

        self._lbl_desglose = QLabel("—")
        self._lbl_desglose.setStyleSheet("color:#C8D0E0; font-size:10px;")
        self._lbl_desglose.setWordWrap(True)
        layout_met.addWidget(self._lbl_desglose)

        layout.addWidget(grp_met)
        layout.addStretch()

        # Estado interno
        self._filas: list[_FilaUnidad] = []

    # ---- helpers de UI ------------------------------------------------------

    def _fila_metrica(self, layout: QVBoxLayout, etiqueta: str) -> QLabel:
        fila = QHBoxLayout()
        lbl_et = QLabel(etiqueta)
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

        # Leer tipologías de la primera planta tipo disponible
        plantas = proyecto.edificio.plantas
        if not plantas:
            tipologias: list[TipoUnidad] = [TipoUnidad.DOS_AMBIENTES]
        else:
            from bim_generador.nucleo.motor_parametros import TipoPlanta
            planta_ref = next(
                (p for p in plantas if p.tipo_planta == TipoPlanta.PLANTA_TIPO),
                plantas[0],
            )
            tipologias = [u.tipologia for u in planta_ref.unidades]
            if not tipologias:
                tipologias = [TipoUnidad.DOS_AMBIENTES]

        self._reconstruir_filas(tipologias)
        self._actualizar_metricas()

    # ---- gestión de filas ---------------------------------------------------

    def _reconstruir_filas(self, tipologias: list[TipoUnidad]) -> None:
        """Elimina todas las filas actuales y crea las nuevas."""
        self._limpiar_filas()
        for tip in tipologias:
            self._crear_fila(tip)
        self._actualizar_spin_preview()

    def _limpiar_filas(self) -> None:
        """Elimina todas las filas del layout (excepto el stretch final)."""
        for fila in self._filas:
            self._layout_filas.removeWidget(fila)
            fila.deleteLater()
        self._filas.clear()

    def _crear_fila(self, tipologia: TipoUnidad) -> None:
        """Crea una fila nueva y la inserta antes del stretch."""
        numero = len(self._filas) + 1
        fila   = _FilaUnidad(numero, tipologia)

        # Conectar señales
        fila.combo.currentIndexChanged.connect(self._al_cambiar_mezcla)
        fila.btn_quitar.clicked.connect(lambda _, f=fila: self._quitar_fila(f))

        # Insertar antes del stretch (último ítem del layout)
        pos = self._layout_filas.count() - 1
        self._layout_filas.insertWidget(pos, fila)
        self._filas.append(fila)

    def _quitar_fila(self, fila: _FilaUnidad) -> None:
        """Elimina la fila indicada y actualiza el proyecto."""
        if len(self._filas) <= 1:
            return  # mínimo 1 unidad por planta
        self._layout_filas.removeWidget(fila)
        fila.deleteLater()
        self._filas.remove(fila)
        self._renumerar_filas()
        self._actualizar_spin_preview()
        self._aplicar_cambios()

    def _renumerar_filas(self) -> None:
        """Actualiza los números de las etiquetas de fila tras una eliminación."""
        for i, fila in enumerate(self._filas):
            lbl = fila.layout().itemAt(0).widget()
            if isinstance(lbl, QLabel):
                lbl.setText(f"#{i + 1}:")

    def _actualizar_spin_preview(self) -> None:
        """Ajusta el máximo del spinner de preview al número de unidades."""
        maximo = max(0, len(self._filas) - 1)
        self._spin_preview.setMaximum(maximo)
        self._spin_preview.setValue(min(self._spin_preview.value(), maximo))

    # ---- slots de cambio ----------------------------------------------------

    def _agregar_unidad(self) -> None:
        """Agrega una nueva unidad de 2 ambientes al mix."""
        if self._proyecto is None:
            return
        self._crear_fila(TipoUnidad.DOS_AMBIENTES)
        self._actualizar_spin_preview()
        self._aplicar_cambios()

    def _al_cambiar_mezcla(self) -> None:
        """Llamado cuando cambia la tipología de cualquier combo."""
        if self._proyecto is None:
            return
        self._aplicar_cambios()

    def _al_cambiar_preview(self) -> None:
        """Actualiza la etiqueta de info de la unidad previsualizada y regenera vista."""
        self._actualizar_info_preview()
        # Emitir cambio sin modificar el modelo (solo cambia el contexto de render)
        if self._proyecto is not None:
            self._emitir_cambio()

    def _aplicar_cambios(self) -> None:
        """Sincroniza el mix de tipologías al proyecto y emite el cambio."""
        if self._proyecto is None:
            return

        tipologias = [f.tipologia_seleccionada() for f in self._filas]
        nuevas_unidades = [
            Unidad.desde_tipologia(tip, codigo=chr(65 + i))
            for i, tip in enumerate(tipologias)
        ]
        self._proyecto.edificio.generar_plantas_tipo(nuevas_unidades)

        self._actualizar_metricas()
        self._emitir_cambio()

    # ---- métricas y labels --------------------------------------------------

    def _actualizar_metricas(self) -> None:
        if self._proyecto is None:
            return

        tipologias = [f.tipologia_seleccionada() for f in self._filas]
        cantidad = len(tipologias)

        # Crear unidades temporales para calcular superficies
        unidades_tmp = [Unidad.desde_tipologia(t) for t in tipologias]
        superficies  = [u.superficie_total_m2 for u in unidades_tmp]
        sup_total    = sum(superficies)
        sup_promedio = sup_total / cantidad if cantidad > 0 else 0.0

        self._lbl_cantidad_unidades.setText(f"{cantidad} unidades")
        self._lbl_sup_promedio.setText(f"{sup_promedio:.1f} m²")
        self._lbl_sup_total.setText(f"{sup_total:.1f} m²")

        # Desglose por tipología
        conteo: dict[TipoUnidad, int] = {}
        for t in tipologias:
            conteo[t] = conteo.get(t, 0) + 1
        lineas = [
            f"  {_NOMBRES_TIPOLOGIA[t]}: {n}"
            for t, n in conteo.items()
        ]
        self._lbl_desglose.setText("\n".join(lineas) if lineas else "—")

        self._actualizar_info_preview()

    def _actualizar_info_preview(self) -> None:
        """Muestra la tipología de la unidad seleccionada en el spinner."""
        idx = self._spin_preview.value()
        if 0 <= idx < len(self._filas):
            tip = self._filas[idx].tipologia_seleccionada()
            unidad = Unidad.desde_tipologia(tip)
            self._lbl_preview_info.setText(
                f"{_NOMBRES_TIPOLOGIA[tip]}  —  {unidad.superficie_total_m2:.0f} m²"
            )
        else:
            self._lbl_preview_info.setText("—")
