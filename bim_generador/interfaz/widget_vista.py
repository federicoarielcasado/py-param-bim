"""
widget_vista.py
---------------
Widget PyQt6 que embebe el visualizador pyvista/VTK en la ventana principal.

Se actualiza automáticamente cuando el MotorVista dispara al_cambiar.

Soporta dos modos de visualización que se configuran automáticamente
según las claves presentes en el pv.MultiBlock recibido:

  Modo 3D  (claves "lote" + "plantas"):
    → Perspectiva. Rotación, zoom, pan libre.
    → Usado por: RenderizadorVolumen

  Modo 2D  (claves "lote_base" + "zona_edificable"):
    → Proyección paralela, cámara cenital fija.
    → Pan y zoom habilitados; rotación deshabilitada.
    → Usado por: RenderizadorLote
"""

from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore    import Qt

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTAQT_DISPONIBLE = True
except ImportError:
    PYVISTAQT_DISPONIBLE = False


# Paleta de colores para plantas (se cicla si hay más pisos que colores)
COLORES_PLANTAS = [
    "#4A90D9", "#5BA85F", "#E8A838", "#D95F5F",
    "#9B6BD4", "#4DBFBF", "#D96CB0", "#8B6F47",
]


class WidgetVista(QWidget):
    """
    Widget de vista previa geométrica contextual.

    Embebe un QtInteractor de pyvista para visualización 3D/2D interactiva.
    Incluye fallback a un label si pyvistaqt no está disponible.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._plotter: Optional["QtInteractor"] = None
        self._configurar_ui()

    def _configurar_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if PYVISTAQT_DISPONIBLE:
            self._plotter = QtInteractor(self)
            self._plotter.set_background("#1E1E2E")
            layout.addWidget(self._plotter)
        else:
            lbl = QLabel("⚠ pyvistaqt no instalado\npip install pyvistaqt", self)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #E8A838; font-size: 13px;")
            layout.addWidget(lbl)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # -----------------------------------------------------------------------
    # Punto de entrada principal — dispatcher de modos
    # -----------------------------------------------------------------------

    def actualizar_vista(self, multi_block) -> None:
        """
        Recibe un pv.MultiBlock del MotorVista y lo renderiza.
        Detecta el modo (3D/2D) según las claves del bloque.
        """
        if self._plotter is None or multi_block is None:
            return

        self._plotter.clear()
        claves = list(multi_block.keys())

        if "lote_base" in claves:
            # Vista 2D — planta de implantación
            self._renderizar_lote_2d(multi_block)
        else:
            # Vista 3D — volumen del edificio
            self._renderizar_volumen_3d(multi_block)

    # -----------------------------------------------------------------------
    # Modo 3D — volumen del edificio
    # -----------------------------------------------------------------------

    def _renderizar_volumen_3d(self, multi_block: "pv.MultiBlock") -> None:
        """Renderiza el volumen 3D del edificio con perspectiva."""

        if "lote" in multi_block.keys():
            self._plotter.add_mesh(
                multi_block["lote"],
                color="#2D7A2D",
                opacity=0.3,
                show_edges=True,
                edge_color="#3FAF3F",
            )

        if "plantas" in multi_block.keys():
            plantas_block = multi_block["plantas"]
            for i, nombre in enumerate(plantas_block.keys()):
                color = COLORES_PLANTAS[i % len(COLORES_PLANTAS)]
                self._plotter.add_mesh(
                    plantas_block[nombre],
                    color=color,
                    opacity=0.85,
                    show_edges=True,
                    edge_color="#FFFFFF",
                    line_width=0.5,
                )

        self._plotter.enable_parallel_projection() if False else None
        self._plotter.show_axes()
        self._plotter.reset_camera()
        self._plotter.camera.elevation = 25
        self._plotter.camera.azimuth   = -45

    # -----------------------------------------------------------------------
    # Modo 2D — planta de implantación del lote
    # -----------------------------------------------------------------------

    def _renderizar_lote_2d(self, multi_block: "pv.MultiBlock") -> None:
        """
        Renderiza la planta de implantación en vista cenital 2D.
        Usa proyección paralela y cámara mirando en dirección -Z.
        """

        # Polígono del lote (verde semitransparente)
        if "lote_base" in multi_block.keys():
            m = multi_block["lote_base"]
            if m.n_cells > 0:
                self._plotter.add_mesh(
                    m,
                    color="#2D6A2D",
                    opacity=0.4,
                    show_edges=True,
                    edge_color="#5FAF5F",
                    line_width=2.0,
                )

        # Franjas de retiro (rojo semitransparente)
        if "zona_retiros" in multi_block.keys():
            m = multi_block["zona_retiros"]
            if m.n_cells > 0:
                self._plotter.add_mesh(
                    m,
                    color="#8B2020",
                    opacity=0.35,
                    show_edges=False,
                )

        # Zona edificable (azul claro)
        if "zona_edificable" in multi_block.keys():
            m = multi_block["zona_edificable"]
            if m.n_cells > 0:
                self._plotter.add_mesh(
                    m,
                    color="#2A4A8A",
                    opacity=0.5,
                    show_edges=True,
                    edge_color="#4A90D9",
                    line_width=1.5,
                )

        # Cotas (líneas blancas)
        if "cotas" in multi_block.keys():
            m = multi_block["cotas"]
            if m.n_cells > 0:
                self._plotter.add_mesh(
                    m,
                    color="#C8D0E0",
                    line_width=1.5,
                    opacity=0.8,
                )

        # Leyenda textual con dimensiones en el plotter
        self._agregar_etiquetas_lote(multi_block)

        # Cámara cenital con proyección paralela
        self._plotter.enable_parallel_projection()
        self._plotter.view_xy()
        self._plotter.reset_camera()

    def _agregar_etiquetas_lote(self, multi_block: "pv.MultiBlock") -> None:
        """
        Agrega etiquetas de texto flotantes con las dimensiones del lote.
        Se usan las posiciones del polígono del lote para calcular los centros.
        """
        if "lote_base" not in multi_block.keys():
            return

        m = multi_block["lote_base"]
        if m.n_points < 4:
            return

        pts  = m.points
        xmin = float(pts[:, 0].min())
        xmax = float(pts[:, 0].max())
        ymin = float(pts[:, 1].min())
        ymax = float(pts[:, 1].max())
        frente = xmax - xmin
        fondo  = ymax - ymin
        offset = max(frente, fondo) * 0.05

        # Etiqueta frente (centro inferior)
        self._plotter.add_point_labels(
            points=[[xmin + frente / 2, ymin - offset * 1.2, 0.05]],
            labels=[f"  frente: {frente:.1f} m  "],
            font_size=10,
            text_color="#E8E8FF",
            bold=False,
            show_points=False,
            always_visible=True,
        )

        # Etiqueta fondo (centro derecho)
        self._plotter.add_point_labels(
            points=[[xmax + offset * 1.2, ymin + fondo / 2, 0.05]],
            labels=[f"  fondo: {fondo:.1f} m  "],
            font_size=10,
            text_color="#E8E8FF",
            bold=False,
            show_points=False,
            always_visible=True,
        )

        # Nota de retiros (esquina superior izquierda)
        if "zona_retiros" in multi_block.keys():
            mr = multi_block["zona_retiros"]
            if mr.n_cells > 0:
                self._plotter.add_point_labels(
                    points=[[xmin, ymax + offset * 0.5, 0.05]],
                    labels=["  ■ retiros  "],
                    font_size=9,
                    text_color="#C87070",
                    bold=False,
                    show_points=False,
                    always_visible=True,
                )

        # Nota zona edificable
        if "zona_edificable" in multi_block.keys():
            me = multi_block["zona_edificable"]
            if me.n_cells > 0:
                self._plotter.add_point_labels(
                    points=[[xmin, ymax + offset * 1.5, 0.05]],
                    labels=["  ■ edificable  "],
                    font_size=9,
                    text_color="#7090C8",
                    bold=False,
                    show_points=False,
                    always_visible=True,
                )

    # -----------------------------------------------------------------------
    # Utilidades
    # -----------------------------------------------------------------------

    def limpiar(self) -> None:
        """Limpia el plotter sin cerrar el widget."""
        if self._plotter:
            self._plotter.clear()

    def closeEvent(self, event) -> None:
        if self._plotter:
            self._plotter.close()
        super().closeEvent(event)
