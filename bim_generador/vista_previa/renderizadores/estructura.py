"""
estructura.py
-------------
Renderizador de grilla estructural con columnas y vigas.

Vista asociada: SeccionActiva.ESTRUCTURA

Genera la vista en planta de la grilla estructural del edificio mostrando:
    - Contorno de la huella de planta (perímetro edificable)
    - Posición de columnas en los nodos de la grilla (cuadrados a escala)
    - Líneas de grilla (vigas en X e Y)
    - Etiquetas con el número de columnas y módulos

El MultiBlock retornado contiene la clave "grilla_estructura" como
marker de dispatch para WidgetVista, más las geometrías:
    "grilla_estructura" → marker (PolyData vacío)
    "contorno"          → contorno de planta (PolyData)
    "columnas"          → MultiBlock con un PolyData por columna
    "grilla_x"          → líneas en dirección X (PolyData)
    "grilla_y"          → líneas en dirección Y (PolyData)
    "etiquetas"         → PolyData con centroides de columnas y:
                            point_data["col_int"] (int, índice de columna)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

try:
    import pyvista as pv
    import numpy as np
    PYVISTA_DISPONIBLE = True
except ImportError:
    PYVISTA_DISPONIBLE = False

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


class RenderizadorEstructura:
    """
    Renderizador de grilla estructural 2D.

    Uso:
        render = RenderizadorEstructura()
        mb = render.renderizar(proyecto)
        # mb["columnas"]  → MultiBlock con un PolyData por columna
        # mb["grilla_x"]  → PolyData con líneas en X
        # mb["grilla_y"]  → PolyData con líneas en Y
    """

    def renderizar(
        self,
        proyecto: "Proyecto",
        contexto: Optional[dict] = None,
    ) -> "pv.MultiBlock | None":
        if not PYVISTA_DISPONIBLE:
            return None

        ed  = proyecto.edificio
        est = ed.estructura

        W = max(proyecto.lote.frente_m - 2.0 * ed.retiro_lateral_m, 5.0)
        D = max(
            proyecto.lote.fondo_m - ed.retiro_frontal_m - ed.retiro_posterior_m,
            8.0,
        )

        mx = est.modulo_x_m
        my = est.modulo_y_m
        sc = est.seccion_columna_m / 2   # semilado del cuadrado de columna

        # Posiciones de grilla
        xs = self._posiciones_grilla(mx, W)
        ys = self._posiciones_grilla(my, D)

        mb = pv.MultiBlock()
        mb["grilla_estructura"] = pv.PolyData()   # marker de dispatch
        mb["contorno"]          = self._contorno(W, D)
        mb["columnas"], mb["etiquetas"] = self._columnas(xs, ys, sc)
        mb["grilla_x"]          = self._lineas_x(xs, D)
        mb["grilla_y"]          = self._lineas_y(ys, W)
        return mb

    @staticmethod
    def tipo_vista() -> str:
        return "grilla_estructura_2d"

    # -----------------------------------------------------------------------
    # Helpers privados
    # -----------------------------------------------------------------------

    @staticmethod
    def _posiciones_grilla(modulo: float, largo: float) -> list[float]:
        """Genera las posiciones de nodos de grilla a intervalos de módulo."""
        if modulo <= 0:
            return [0.0]
        pos = []
        x = 0.0
        while x <= largo + 1e-6:
            pos.append(round(x, 6))
            x += modulo
        return pos

    @staticmethod
    def _contorno(W: float, D: float) -> "pv.PolyData":
        puntos = np.array([
            [0.0, 0.0, 0.0],
            [W,   0.0, 0.0],
            [W,   D,   0.0],
            [0.0, D,   0.0],
        ], dtype=float)
        return pv.PolyData(puntos, np.array([4, 0, 1, 2, 3]))

    def _columnas(
        self,
        xs: list[float],
        ys: list[float],
        sc: float,
    ) -> tuple["pv.MultiBlock", "pv.PolyData"]:
        columnas_mb = pv.MultiBlock()
        centroides: list = []
        indices:    list = []

        idx = 0
        for x in xs:
            for y in ys:
                mesh = self._rect(x - sc, y - sc, x + sc, y + sc)
                mesh.cell_data["col_int"] = [idx]
                columnas_mb[f"col_{idx}"] = mesh
                centroides.append([x, y, 0.02])
                indices.append(idx)
                idx += 1

        etiquetas = pv.PolyData()
        if centroides:
            etiquetas.points    = np.array(centroides, dtype=float)
            etiquetas["col_int"] = np.array(indices,   dtype=int)

        return columnas_mb, etiquetas

    @staticmethod
    def _lineas_x(xs: list[float], D: float) -> "pv.PolyData":
        """Líneas verticales (en dirección Y) para cada X de grilla."""
        if not xs:
            return pv.PolyData()
        puntos = []
        lineas = []
        for x in xs:
            i = len(puntos)
            puntos.extend([[x, 0.0, 0.0], [x, D, 0.0]])
            lineas.extend([2, i, i + 1])
        return pv.PolyData(
            np.array(puntos, dtype=float),
            lines=np.array(lineas, dtype=int),
        )

    @staticmethod
    def _lineas_y(ys: list[float], W: float) -> "pv.PolyData":
        """Líneas horizontales (en dirección X) para cada Y de grilla."""
        if not ys:
            return pv.PolyData()
        puntos = []
        lineas = []
        for y in ys:
            i = len(puntos)
            puntos.extend([[0.0, y, 0.0], [W, y, 0.0]])
            lineas.extend([2, i, i + 1])
        return pv.PolyData(
            np.array(puntos, dtype=float),
            lines=np.array(lineas, dtype=int),
        )

    @staticmethod
    def _rect(x0: float, y0: float, x1: float, y1: float, z: float = 0.0) -> "pv.PolyData":
        puntos = np.array([
            [x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z],
        ], dtype=float)
        return pv.PolyData(puntos, np.array([4, 0, 1, 2, 3]))
