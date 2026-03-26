"""
circulacion.py
--------------
Renderizador de planta tipo 2D con distribución de unidades.

Vista asociada: SeccionActiva.CIRCULACION

Genera la vista en planta del piso seleccionado mostrando:
    - Contorno de la huella de planta (perímetro edificable)
    - Núcleo vertical (escaleras + ascensor)
    - Pasillo de distribución central
    - Unidades funcionales coloreadas por tipología
    - Etiquetas con código y superficie de cada unidad

El MultiBlock retornado contiene la clave "planta_circulacion" como
marker de dispatch para WidgetVista, más las geometrías:
    "planta_circulacion" → marker (PolyData vacío)
    "contorno"           → contorno de planta (PolyData)
    "core"               → núcleo vertical (PolyData)
    "pasillo"            → pasillo de distribución (PolyData)
    "unidades"           → MultiBlock con un PolyData por unidad
    "etiquetas"          → PolyData con centroides de unidades y:
                             point_data["tipologia_int"] (int)
                             point_data["superficie_m2"] (float)
                             point_data["lado_int"]      (0=sur, 1=norte)

Contexto esperado:
    {"planta_idx": N}   (índice de planta; 0 = PB)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

try:
    import pyvista as pv
    import numpy as np
    PYVISTA_DISPONIBLE = True
except ImportError:
    PYVISTA_DISPONIBLE = False

from bim_generador.nucleo.motor_parametros import TipoUnidad
from bim_generador.generadores.planta import GeneradorPlanta, GeometriaPlanta

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


# ---------------------------------------------------------------------------
# Mapeo TipoUnidad → entero para cell/point data
# ---------------------------------------------------------------------------

_TIPOLOGIA_A_INT: dict[TipoUnidad, int] = {
    TipoUnidad.MONOAMBIENTE:      0,
    TipoUnidad.DOS_AMBIENTES:     1,
    TipoUnidad.TRES_AMBIENTES:    2,
    TipoUnidad.CUATRO_AMBIENTES:  3,
    TipoUnidad.DUPLEX:            4,
}


class RenderizadorCirculacion:
    """
    Renderizador de planta 2D con distribución de unidades y circulación.

    Uso:
        render = RenderizadorCirculacion()
        mb = render.renderizar(proyecto, contexto={"planta_idx": 0})
        # mb["unidades"] → MultiBlock con un PolyData por unidad
        # mb["etiquetas"] → PolyData con centroides y metadata
    """

    def renderizar(
        self,
        proyecto: "Proyecto",
        contexto: Optional[dict] = None,
    ) -> "pv.MultiBlock | None":
        if not PYVISTA_DISPONIBLE:
            return None

        plantas = proyecto.edificio.plantas
        if not plantas:
            return self._bloque_vacio()

        contexto   = contexto or {}
        idx        = int(contexto.get("planta_idx", 0))
        idx        = max(0, min(idx, len(plantas) - 1))

        gen  = GeneradorPlanta()
        geom = gen.generar(plantas[idx], proyecto.lote, proyecto.edificio)

        return self._a_pyvista(geom)

    @staticmethod
    def tipo_vista() -> str:
        return "planta_circulacion_2d"

    # -----------------------------------------------------------------------
    # Construcción del MultiBlock
    # -----------------------------------------------------------------------

    def _bloque_vacio(self) -> "pv.MultiBlock":
        mb = pv.MultiBlock()
        mb["planta_circulacion"] = pv.PolyData()
        mb["contorno"]           = pv.PolyData()
        mb["core"]               = pv.PolyData()
        mb["pasillo"]            = pv.PolyData()
        mb["unidades"]           = pv.MultiBlock()
        mb["etiquetas"]          = pv.PolyData()
        return mb

    def _a_pyvista(self, geom: GeometriaPlanta) -> "pv.MultiBlock":
        mb = pv.MultiBlock()
        mb["planta_circulacion"] = pv.PolyData()   # marker de dispatch
        mb["contorno"]           = self._contorno(geom)
        mb["core"]               = self._rect_polydata(
            geom.core.x, geom.core.y,
            geom.core.x + geom.core.ancho,
            geom.core.y + geom.core.alto,
        )
        mb["pasillo"]            = self._rect_polydata(
            geom.pasillo.x, geom.pasillo.y,
            geom.pasillo.x + geom.pasillo.ancho,
            geom.pasillo.y + geom.pasillo.alto,
        )
        mb["unidades"], mb["etiquetas"] = self._unidades(geom)
        return mb

    @staticmethod
    def _contorno(geom: GeometriaPlanta) -> "pv.PolyData":
        """Crea el contorno perimetral de la planta como rectángulo."""
        W, D = geom.ancho_total, geom.fondo_total
        puntos = np.array([
            [0.0, 0.0, 0.0],
            [W,   0.0, 0.0],
            [W,   D,   0.0],
            [0.0, D,   0.0],
        ], dtype=float)
        caras = np.array([4, 0, 1, 2, 3])
        return pv.PolyData(puntos, caras)

    @staticmethod
    def _rect_polydata(
        x0: float, y0: float,
        x1: float, y1: float,
        z: float = 0.0,
    ) -> "pv.PolyData":
        puntos = np.array([
            [x0, y0, z],
            [x1, y0, z],
            [x1, y1, z],
            [x0, y1, z],
        ], dtype=float)
        caras = np.array([4, 0, 1, 2, 3])
        return pv.PolyData(puntos, caras)

    def _unidades(
        self,
        geom: GeometriaPlanta,
    ) -> tuple["pv.MultiBlock", "pv.PolyData"]:
        """Genera los meshes de unidades y los centroides para etiquetas."""
        unidades_mb = pv.MultiBlock()
        centroides:     list = []
        tipologias_int: list = []
        superficies:    list = []
        lados_int:      list = []

        for i, u_geom in enumerate(geom.unidades):
            mesh = self._rect_polydata(
                u_geom.x, u_geom.y,
                u_geom.x + u_geom.ancho,
                u_geom.y + u_geom.alto,
            )
            tip_int = _TIPOLOGIA_A_INT.get(u_geom.unidad.tipologia, 1)
            mesh.cell_data["tipologia_int"] = [tip_int]
            mesh.cell_data["superficie_m2"] = [round(u_geom.unidad.superficie_total_m2, 2)]
            unidades_mb[f"unidad_{i}"] = mesh

            centroides.append([u_geom.cx, u_geom.cy, 0.02])
            tipologias_int.append(tip_int)
            superficies.append(round(u_geom.unidad.superficie_total_m2, 2))
            lados_int.append(0 if u_geom.lado == "sur" else 1)

        etiquetas = pv.PolyData()
        if centroides:
            etiquetas.points               = np.array(centroides,     dtype=float)
            etiquetas["tipologia_int"]     = np.array(tipologias_int, dtype=int)
            etiquetas["superficie_m2"]     = np.array(superficies,    dtype=float)
            etiquetas["lado_int"]          = np.array(lados_int,      dtype=int)

        return unidades_mb, etiquetas
