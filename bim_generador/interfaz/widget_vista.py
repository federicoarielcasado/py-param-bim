"""
widget_vista.py
---------------
Widget PyQt6 que embebe el visualizador pyvista/VTK en la ventana principal.

Se actualiza automáticamente cuando el MotorVista dispara al_cambiar.
Soporta interacción 3D básica: rotación, zoom, pan.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore    import Qt

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTAQT_DISPONIBLE = True
except ImportError:
    PYVISTAQT_DISPONIBLE = False

if TYPE_CHECKING:
    pass


# Paleta de colores para plantas (se cicla si hay más pisos que colores)
COLORES_PLANTAS = [
    "#4A90D9", "#5BA85F", "#E8A838", "#D95F5F",
    "#9B6BD4", "#4DBFBF", "#D96CB0", "#8B6F47",
]


class WidgetVista(QWidget):
    """
    Widget de vista previa geométrica contextual.

    Embebe un QtInteractor de pyvista para visualización 3D interactiva.
    Incluye fallback a un label de texto si pyvistaqt no está disponible.
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
            self._plotter.set_background("#1E1E2E")  # fondo oscuro estilo BIM
            layout.addWidget(self._plotter)
        else:
            lbl = QLabel("⚠ pyvistaqt no instalado\npip install pyvistaqt", self)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #E8A838; font-size: 13px;")
            layout.addWidget(lbl)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def actualizar_vista(self, multi_block) -> None:
        """
        Recibe un pv.MultiBlock del MotorVista y lo renderiza.
        Es el callback que conecta el MotorVista con la GUI.
        """
        if self._plotter is None or multi_block is None:
            return

        self._plotter.clear()

        # Renderizar el lote (plano semitransparente verde)
        if "lote" in multi_block.keys():
            self._plotter.add_mesh(
                multi_block["lote"],
                color="#2D7A2D",
                opacity=0.3,
                show_edges=True,
                edge_color="#3FAF3F",
                label="Lote",
            )

        # Renderizar plantas con colores alternados
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

        # Ejes y configuración de cámara
        self._plotter.show_axes()
        self._plotter.reset_camera()
        self._plotter.camera.elevation = 25
        self._plotter.camera.azimuth   = -45

    def limpiar(self) -> None:
        """Limpia el plotter sin cerrar el widget."""
        if self._plotter:
            self._plotter.clear()

    def closeEvent(self, event) -> None:
        """Cierra el plotter de pyvista correctamente al cerrar el widget."""
        if self._plotter:
            self._plotter.close()
        super().closeEvent(event)
