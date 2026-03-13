"""
main.py
-------
Punto de entrada de la aplicación BIM Parametric Building Generator.

Uso:
    python main.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore    import Qt
from bim_generador.interfaz.ventana_principal import VentanaPrincipal


def main() -> None:
    # En Windows, necesario para que pyvista/VTK funcione correctamente con Qt
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setApplicationName("BIM Generator")
    app.setOrganizationName("FedeCasado")

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
