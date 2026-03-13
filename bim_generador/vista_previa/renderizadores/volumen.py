"""
volumen.py
----------
Renderizador de volumen 3D del edificio (sección GENERAL).

Genera un mesh pyvista con la caja volumétrica del edificio sobre el lote,
con subdivisión por plantas. Es el primer renderizador funcional del sistema.

Muestra:
  - Polígono del lote (plano verde)
  - Huella del edificio (según retiros)
  - Volumen extruido por piso, con alternancia de colores por planta
"""

from __future__ import annotations
from typing import TYPE_CHECKING

try:
    import pyvista as pv
    import numpy as np
    PYVISTA_DISPONIBLE = True
except ImportError:
    PYVISTA_DISPONIBLE = False

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class RenderizadorVolumen:
    """
    Renderizador de volumen 3D simple (bounding box por planta).

    Retorna un pv.MultiBlock listo para agregar a un plotter pyvista.
    """

    def renderizar(self, proyecto: "Proyecto") -> "pv.MultiBlock | None":
        """
        Genera el conjunto de meshes para la vista previa volumétrica.

        Retorna:
            pv.MultiBlock con: 'lote', 'edificio', 'plantas'
            O None si pyvista no está disponible.
        """
        if not PYVISTA_DISPONIBLE:
            return None

        bloques = pv.MultiBlock()

        lote_mesh    = self._generar_lote(proyecto)
        edificio_mesh = self._generar_volumenes_plantas(proyecto)

        bloques["lote"]    = lote_mesh
        bloques["plantas"] = edificio_mesh

        return bloques

    # ---- helpers privados --------------------------------------------------

    def _generar_lote(self, proyecto: "Proyecto") -> "pv.PolyData":
        """Genera el plano del lote como mesh plano en Z=0."""
        import numpy as np

        f = proyecto.lote.frente_m
        d = proyecto.lote.fondo_m

        # Rectángulo del lote centrado en el origen
        puntos = np.array([
            [0.0,  0.0, 0.0],
            [f,    0.0, 0.0],
            [f,    d,   0.0],
            [0.0,  d,   0.0],
        ])
        caras = np.array([4, 0, 1, 2, 3])
        mesh = pv.PolyData(puntos, caras)
        mesh["tipo"] = ["lote"] * mesh.n_cells
        return mesh

    def _generar_volumenes_plantas(self, proyecto: "Proyecto") -> "pv.MultiBlock":
        """Genera un box por planta del edificio, apilados verticalmente."""
        import numpy as np

        bloques = pv.MultiBlock()
        ed      = proyecto.edificio
        lote    = proyecto.lote

        # Huella del edificio (descontando retiros)
        x0 = ed.retiro_lateral_m
        y0 = ed.retiro_posterior_m
        x1 = lote.frente_m - ed.retiro_lateral_m
        y1 = lote.fondo_m  - ed.retiro_frontal_m

        if x1 <= x0 or y1 <= y0:
            return bloques  # retiros exceden el lote

        z_actual = 0.0
        for i, planta in enumerate(ed.plantas):
            alto = planta.altura_libre_m + ed.estructura.espesor_losa_m
            box  = pv.Box(bounds=(x0, x1, y0, y1, z_actual, z_actual + alto))
            box["planta"] = [planta.nombre] * box.n_cells
            bloques[f"planta_{i}"] = box
            z_actual += alto

        return bloques
