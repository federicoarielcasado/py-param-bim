"""
lote.py
-------
Renderizador de vista superior del lote (planta de implantación).

Genera un pv.MultiBlock con todos los elementos necesarios para la
vista 2D top-down del lote:

  - Polígono del lote (verde relleno)
  - Zona no edificable — franjas de retiro (rojo semitransparente)
  - Zona edificable — área disponible (azul semitransparente)
  - Huella real del edificio (calculada con los retiros actuales)
  - Líneas de cota con dimensiones de frente y fondo
  - Norte magnético (orientación del lote)

El MultiBlock incluye la clave especial "_meta/tipo_vista" = "lote_2d"
para que el WidgetVista sepa que debe configurar la cámara cenital.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

try:
    import pyvista as pv
    PYVISTA_DISPONIBLE = True
except ImportError:
    PYVISTA_DISPONIBLE = False

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto


# Offset en Z para evitar z-fighting entre polígonos coplanares
_Z_LOTE       = 0.00
_Z_RETIRO     = 0.01
_Z_EDIFICABLE = 0.02
_Z_HUELLA     = 0.03
_Z_COTAS      = 0.04


def _rectangulo(x0: float, y0: float, x1: float, y1: float, z: float) -> "pv.PolyData":
    """Crea un polígono rectangular como pv.PolyData relleno."""
    puntos = np.array([
        [x0, y0, z],
        [x1, y0, z],
        [x1, y1, z],
        [x0, y1, z],
    ], dtype=float)
    caras = np.array([4, 0, 1, 2, 3])
    return pv.PolyData(puntos, caras)


def _linea(p0: list, p1: list, z: float) -> "pv.PolyData":
    """Crea un segmento de línea como pv.PolyData."""
    puntos = np.array([[p0[0], p0[1], z], [p1[0], p1[1], z]], dtype=float)
    lineas = np.array([2, 0, 1])
    return pv.PolyData(puntos, lines=lineas)


class RenderizadorLote:
    """
    Renderizador de planta de implantación (vista 2D superior).

    Retorna un pv.MultiBlock con los layers del plano:
        "lote_base"       → polígono del lote (relleno verde)
        "zona_retiros"    → franjas de retiro (rojo semitransparente)
        "zona_edificable" → área edificable (azul claro semitransparente)
        "huella_edificio" → huella real del edificio (azul oscuro)
        "cotas_frente"    → línea de cota del frente del lote
        "cotas_fondo"     → línea de cota del fondo del lote
    """

    def renderizar(self, proyecto: "Proyecto") -> "pv.MultiBlock | None":
        if not PYVISTA_DISPONIBLE:
            return None

        bloques = pv.MultiBlock()
        bloques["lote_base"]       = self._lote_base(proyecto)
        bloques["zona_retiros"]    = self._zona_retiros(proyecto)
        bloques["zona_edificable"] = self._zona_edificable(proyecto)
        bloques["huella_edificio"] = self._huella_edificio(proyecto)
        bloques["cotas"]           = self._cotas(proyecto)

        return bloques

    # ---- Capas del render --------------------------------------------------

    def _lote_base(self, proyecto: "Proyecto") -> "pv.PolyData":
        """Polígono del lote completo."""
        f = proyecto.lote.frente_m
        d = proyecto.lote.fondo_m
        return _rectangulo(0, 0, f, d, _Z_LOTE)

    def _zona_retiros(self, proyecto: "Proyecto") -> "pv.PolyData":
        """
        Genera las franjas de retiro como la diferencia visual entre
        el lote y la zona edificable. Se representa como 4 rectángulos
        (uno por lado: frontal, posterior, lateral izq, lateral der).
        """
        f    = proyecto.lote.frente_m
        d    = proyecto.lote.fondo_m
        ed   = proyecto.edificio
        r_fr = ed.retiro_frontal_m
        r_po = ed.retiro_posterior_m
        r_la = ed.retiro_lateral_m

        franjas: list["pv.PolyData"] = []

        # Retiro frontal (borde Y superior)
        if r_fr > 0:
            franjas.append(_rectangulo(0, d - r_fr, f, d, _Z_RETIRO))

        # Retiro posterior (borde Y inferior)
        if r_po > 0:
            franjas.append(_rectangulo(0, 0, f, r_po, _Z_RETIRO))

        # Retiro lateral izquierdo (borde X=0)
        if r_la > 0:
            franjas.append(_rectangulo(0, r_po, r_la, d - r_fr, _Z_RETIRO))

        # Retiro lateral derecho (borde X=frente)
        if r_la > 0:
            franjas.append(_rectangulo(f - r_la, r_po, f, d - r_fr, _Z_RETIRO))

        if not franjas:
            # Sin retiros: retornar mesh vacío
            return pv.PolyData()

        return pv.merge(franjas)

    def _zona_edificable(self, proyecto: "Proyecto") -> "pv.PolyData | None":
        """Área edificable después de aplicar los retiros."""
        f    = proyecto.lote.frente_m
        d    = proyecto.lote.fondo_m
        ed   = proyecto.edificio
        x0   = ed.retiro_lateral_m
        y0   = ed.retiro_posterior_m
        x1   = f - ed.retiro_lateral_m
        y1   = d - ed.retiro_frontal_m

        if x1 <= x0 or y1 <= y0:
            return pv.PolyData()  # retiros exceden el lote

        return _rectangulo(x0, y0, x1, y1, _Z_EDIFICABLE)

    def _huella_edificio(self, proyecto: "Proyecto") -> "pv.PolyData":
        """
        Huella real del edificio. Por ahora es igual a la zona edificable,
        ya que el edificio ocupa todo el espacio disponible dentro de los
        retiros. En Fase 2, se calculará la huella exacta de la PB.
        """
        return self._zona_edificable(proyecto)

    def _cotas(self, proyecto: "Proyecto") -> "pv.PolyData":
        """
        Líneas de cota para indicar las dimensiones del lote.
        Genera dos líneas paralelas a los bordes con offset exterior.
        """
        f = proyecto.lote.frente_m
        d = proyecto.lote.fondo_m
        offset = max(f, d) * 0.05  # 5% del lado mayor como offset

        segmentos: list["pv.PolyData"] = []

        # Cota del frente (paralela al eje X, debajo del lote)
        segmentos.append(_linea([0, -offset], [f, -offset], _Z_COTAS))

        # Cota del fondo (paralela al eje Y, a la derecha del lote)
        segmentos.append(_linea([f + offset, 0], [f + offset, d], _Z_COTAS))

        # Ticks verticales para la cota de frente
        segmentos.append(_linea([0,  -offset * 0.3], [0,  -offset * 1.3], _Z_COTAS))
        segmentos.append(_linea([f,  -offset * 0.3], [f,  -offset * 1.3], _Z_COTAS))

        # Ticks horizontales para la cota de fondo
        segmentos.append(_linea([f + offset * 0.3, 0], [f + offset * 1.3, 0], _Z_COTAS))
        segmentos.append(_linea([f + offset * 0.3, d], [f + offset * 1.3, d], _Z_COTAS))

        return pv.merge(segmentos)

    # ---- Metadatos para el WidgetVista ------------------------------------

    @staticmethod
    def tipo_vista() -> str:
        """Identificador del tipo de vista que genera este renderizador."""
        return "lote_2d"
