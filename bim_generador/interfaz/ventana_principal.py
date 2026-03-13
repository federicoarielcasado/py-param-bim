"""
ventana_principal.py
--------------------
Ventana principal del BIM Parametric Building Generator.

Layout de tres columnas:
  ┌────────────────┬──────────────────────────────┬──────────────────┐
  │  Navegación    │  Panel de configuración       │  Vista previa 3D │
  │  (barra lat.)  │  (cambia por sección)         │  (contextual)    │
  └────────────────┴──────────────────────────────┴──────────────────┘

La sección activa determina qué panel se muestra y qué vista previa se renderiza.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QStatusBar,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui  import QAction, QFont, QIcon

from bim_generador.nucleo.motor_parametros    import Proyecto
from bim_generador.vista_previa.motor         import MotorVista, SeccionActiva
from bim_generador.interfaz.widget_vista      import WidgetVista

# Paneles disponibles
from bim_generador.interfaz.paneles.panel_general import PanelGeneral
from bim_generador.interfaz.paneles.panel_lote    import PanelLote


# Mapa: nombre visible → (clase del panel, SeccionActiva)
SECCIONES: list[tuple[str, type, SeccionActiva]] = [
    ("⚙ General",          PanelGeneral, SeccionActiva.GENERAL),
    ("🏗 Lote",             PanelLote,    SeccionActiva.LOTE),
    # Los paneles siguientes se descomientan a medida que se implementan:
    # ("🏠 Tipologías",    PanelTipologias,   SeccionActiva.TIPOLOGIAS),
    # ("🛋 Ambientes",      PanelUnidad,       SeccionActiva.AMBIENTES),
    # ("🚶 Circulación",   PanelCirculacion,  SeccionActiva.CIRCULACION),
    # ("🏛 Estructura",    PanelEstructura,   SeccionActiva.ESTRUCTURA),
    # ("🪟 Fachada",        PanelFachada,      SeccionActiva.FACHADA),
    # ("🧱 Materiales",    PanelMateriales,   SeccionActiva.MATERIALES),
    # ("📄 Documentación", PanelDocumentacion, SeccionActiva.DOCUMENTACION),
]

# Retardo (ms) para debounce: espera antes de redibujar la vista previa tras un cambio
RETARDO_MS = 400


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la aplicación.

    Flujo de datos:
        Usuario modifica parámetro
            → Panel emite parametros_cambiados
            → _al_cambiar_parametros() inicia timer de debounce
            → Timer dispara _regenerar_vista()
            → MotorVista.actualizar() genera el mesh
            → WidgetVista.actualizar_vista() lo renderiza
    """

    def __init__(self):
        super().__init__()
        self._proyecto = Proyecto.desde_predeterminados("Nuevo Proyecto BIM")
        self._motor   = MotorVista()
        self._paneles: dict[str, object] = {}
        self._panel_activo = None

        # Timer de debounce para no redibujar en cada keystroke
        self._timer_vista = QTimer(self)
        self._timer_vista.setSingleShot(True)
        self._timer_vista.timeout.connect(self._regenerar_vista)

        self._configurar_ui()
        self._configurar_menus()
        self._conectar_motor()
        self._cargar_proyecto(self._proyecto)

    # -----------------------------------------------------------------------
    # Construcción de la UI
    # -----------------------------------------------------------------------

    def _configurar_ui(self) -> None:
        self.setWindowTitle("BIM Parametric Building Generator")
        self.setMinimumSize(1280, 720)
        self.resize(1440, 850)
        self._aplicar_estilo()

        central = QWidget()
        self.setCentralWidget(central)
        layout_raiz = QHBoxLayout(central)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        # Splitter principal: barra lateral | panel | vista previa
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # ---- Barra lateral (navegación por secciones) ----------------------
        self._barra_lateral = self._crear_barra_lateral()
        splitter.addWidget(self._barra_lateral)

        # ---- Stack de paneles de configuración -----------------------------
        self._contenedor_panel = QWidget()
        self._layout_panel    = QVBoxLayout(self._contenedor_panel)
        self._layout_panel.setContentsMargins(0, 0, 0, 0)
        self._contenedor_panel.setMinimumWidth(280)
        self._contenedor_panel.setMaximumWidth(420)
        splitter.addWidget(self._contenedor_panel)

        # ---- Widget de vista previa ----------------------------------------
        self._vista = WidgetVista()
        splitter.addWidget(self._vista)

        # Proporciones iniciales: barra lateral 160 | panel 320 | vista resto
        splitter.setSizes([160, 320, 800])
        layout_raiz.addWidget(splitter)

        # ---- Barra de estado -----------------------------------------------
        self.statusBar().showMessage("Listo")

    def _crear_barra_lateral(self) -> QListWidget:
        """Crea la lista de navegación lateral."""
        lista = QListWidget()
        lista.setFixedWidth(160)
        lista.setStyleSheet("""
            QListWidget {
                background-color: #13131F;
                border: none;
                color: #C8D0E0;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-bottom: 1px solid #2A2A40;
            }
            QListWidget::item:selected {
                background-color: #2A3A5C;
                color: #7EB8F7;
                border-left: 3px solid #4A90D9;
            }
            QListWidget::item:hover:!selected {
                background-color: #1E1E2E;
            }
        """)

        for nombre, _clase, _seccion in SECCIONES:
            item = QListWidgetItem(nombre)
            lista.addItem(item)

        lista.currentRowChanged.connect(self._al_cambiar_seccion)
        lista.setCurrentRow(0)
        return lista

    def _configurar_menus(self) -> None:
        """Crea la barra de menús."""
        menubar = self.menuBar()

        # Menú Archivo
        menu_archivo = menubar.addMenu("&Archivo")

        act_nuevo = QAction("&Nuevo proyecto", self)
        act_nuevo.setShortcut("Ctrl+N")
        act_nuevo.triggered.connect(self._nuevo_proyecto)
        menu_archivo.addAction(act_nuevo)

        act_abrir = QAction("&Abrir...", self)
        act_abrir.setShortcut("Ctrl+O")
        act_abrir.triggered.connect(self._abrir_proyecto)
        menu_archivo.addAction(act_abrir)

        act_guardar = QAction("&Guardar", self)
        act_guardar.setShortcut("Ctrl+S")
        act_guardar.triggered.connect(self._guardar_proyecto)
        menu_archivo.addAction(act_guardar)

        menu_archivo.addSeparator()

        act_salir = QAction("&Salir", self)
        act_salir.setShortcut("Ctrl+Q")
        act_salir.triggered.connect(self.close)
        menu_archivo.addAction(act_salir)

        # Menú Vista
        menu_vista = menubar.addMenu("&Vista")

        act_reset_cam = QAction("Reiniciar cámara", self)
        act_reset_cam.setShortcut("Ctrl+R")
        act_reset_cam.triggered.connect(self._reiniciar_camara)
        menu_vista.addAction(act_reset_cam)

    def _aplicar_estilo(self) -> None:
        """Aplica la hoja de estilos global de la ventana."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E2E;
            }
            QGroupBox {
                color: #C8D0E0;
                border: 1px solid #3A3A5C;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 4px;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: #7EB8F7;
            }
            QLabel {
                color: #C8D0E0;
                font-size: 12px;
            }
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
                background-color: #2A2A40;
                color: #E0E8F0;
                border: 1px solid #3A3A5C;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
                border-color: #4A90D9;
            }
            QScrollArea, QWidget#contenedor_panel {
                background-color: #1A1A2E;
                border: none;
            }
            QStatusBar {
                background-color: #13131F;
                color: #7EB8F7;
                font-size: 11px;
            }
            QMenuBar {
                background-color: #13131F;
                color: #C8D0E0;
            }
            QMenuBar::item:selected {
                background-color: #2A3A5C;
            }
            QMenu {
                background-color: #1E1E2E;
                color: #C8D0E0;
                border: 1px solid #3A3A5C;
            }
            QMenu::item:selected {
                background-color: #2A3A5C;
            }
            QSplitter::handle {
                background-color: #3A3A5C;
            }
        """)

    # -----------------------------------------------------------------------
    # Conexión del motor de vista previa
    # -----------------------------------------------------------------------

    def _conectar_motor(self) -> None:
        self._motor.al_cambiar = self._vista.actualizar_vista

    # -----------------------------------------------------------------------
    # Carga y navegación
    # -----------------------------------------------------------------------

    def _cargar_proyecto(self, proyecto: Proyecto) -> None:
        """Carga un proyecto en la ventana y actualiza todos los paneles."""
        self._proyecto = proyecto
        self.setWindowTitle(f"BIM Generator — {proyecto.nombre}")

        for panel in self._paneles.values():
            panel.cargar(proyecto)

        self._regenerar_vista()

    def _al_cambiar_seccion(self, fila: int) -> None:
        """Muestra el panel correspondiente a la sección seleccionada."""
        if fila < 0 or fila >= len(SECCIONES):
            return

        nombre, ClasePanel, seccion = SECCIONES[fila]

        # Crear el panel si no existe todavía
        if nombre not in self._paneles:
            panel = ClasePanel()
            panel.cargar(self._proyecto)
            panel.parametros_cambiados.connect(self._al_cambiar_parametros)
            self._paneles[nombre] = panel

        # Ocultar el panel actual y mostrar el nuevo
        if self._panel_activo:
            self._layout_panel.removeWidget(self._panel_activo)
            self._panel_activo.hide()

        nuevo_panel = self._paneles[nombre]
        self._layout_panel.addWidget(nuevo_panel)
        nuevo_panel.show()
        self._panel_activo = nuevo_panel

        # Cambiar el tipo de vista previa
        self._motor.actualizar(self._proyecto, seccion)
        self.statusBar().showMessage(f"Sección: {nombre}")

    # -----------------------------------------------------------------------
    # Debounce y regeneración de la vista previa
    # -----------------------------------------------------------------------

    def _al_cambiar_parametros(self) -> None:
        """Arranca el timer de debounce al detectar un cambio de parámetro."""
        self._timer_vista.start(RETARDO_MS)
        self.statusBar().showMessage("Recalculando…")

    def _regenerar_vista(self) -> None:
        """Regenera la vista previa con la sección y proyecto actuales."""
        fila = self._barra_lateral.currentRow()
        if 0 <= fila < len(SECCIONES):
            _, _, seccion = SECCIONES[fila]
            self._motor.actualizar(self._proyecto, seccion)
        self.statusBar().showMessage("Listo")

    def _reiniciar_camara(self) -> None:
        if self._vista._plotter:
            self._vista._plotter.reset_camera()

    # -----------------------------------------------------------------------
    # Acciones de Archivo
    # -----------------------------------------------------------------------

    def _nuevo_proyecto(self) -> None:
        respuesta = QMessageBox.question(
            self, "Nuevo proyecto",
            "¿Descartás el proyecto actual y creás uno nuevo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self._paneles.clear()
            self._panel_activo = None
            self._cargar_proyecto(Proyecto.desde_predeterminados("Nuevo Proyecto BIM"))
            self._barra_lateral.setCurrentRow(0)

    def _abrir_proyecto(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir proyecto", "", "JSON (*.json)"
        )
        if ruta:
            try:
                with open(ruta, encoding="utf-8") as f:
                    json_str = f.read()
                proyecto = Proyecto.desde_json(json_str)
                self._paneles.clear()
                self._panel_activo = None
                self._cargar_proyecto(proyecto)
                self._barra_lateral.setCurrentRow(0)
                self.statusBar().showMessage(f"Proyecto cargado: {ruta}")
            except Exception as e:
                QMessageBox.critical(self, "Error al abrir", str(e))

    def _guardar_proyecto(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar proyecto", f"{self._proyecto.nombre}.json", "JSON (*.json)"
        )
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(self._proyecto.a_json())
                self.statusBar().showMessage(f"Guardado: {ruta}")
            except Exception as e:
                QMessageBox.critical(self, "Error al guardar", str(e))

    def closeEvent(self, event) -> None:
        self._vista.closeEvent(event)
        super().closeEvent(event)
