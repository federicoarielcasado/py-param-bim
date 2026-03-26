"""
planta.py
---------
Generador de layout de planta tipo.

Toma Lote, Edificio y Planta y produce la geometría 2D:
posición de cada unidad, pasillo central y núcleo vertical.

Salida: GeometriaPlanta — estructura de datos pura, sin dependencia de pyvista.
El RenderizadorCirculacion consume esta estructura para generar la vista previa.

Algoritmo de distribución:
    ┌────────────────────────────────────────┐
    │  [Unidad N1]  [Unidad N2]  [Unidad N3] │  ← lado norte
    │  ──────────── PASILLO ─────────────── │
    │  [Unidad S1]  [Unidad S2]              │  ← lado sur
    │[CORE]                                  │
    └────────────────────────────────────────┘
    Origen (0,0) en esquina inferior-izquierda.
    X: dirección frente (0 → ancho_total).
    Y: dirección fondo  (0 → fondo_total).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from bim_generador.nucleo.motor_parametros import TipoAmbiente

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import (
        Planta, Lote, Edificio, Unidad, Ambiente,
    )


# ---------------------------------------------------------------------------
# Clasificación de ambientes por zona funcional
# ---------------------------------------------------------------------------

_ZONA_SOCIAL = frozenset({
    TipoAmbiente.LIVING_COMEDOR,
    TipoAmbiente.COCINA,
    TipoAmbiente.ESTUDIO,
})
_ZONA_PRIVADA = frozenset({
    TipoAmbiente.DORMITORIO_SIMPLE,
    TipoAmbiente.DORMITORIO_PRINCIPAL,
})
_ZONA_SERVICIO = frozenset({
    TipoAmbiente.BANIO,
    TipoAmbiente.TOILETTE,
    TipoAmbiente.LAVADERO,
})


# ---------------------------------------------------------------------------
# Estructuras de datos de geometría
# ---------------------------------------------------------------------------

@dataclass
class RectAmbiente:
    """Bounding box 2D de un ambiente dentro de la planta."""
    ambiente: "Ambiente"
    x: float
    y: float
    ancho: float
    alto: float

    @property
    def cx(self) -> float:
        return self.x + self.ancho / 2

    @property
    def cy(self) -> float:
        return self.y + self.alto / 2


@dataclass
class GeometriaUnidad:
    """Layout 2D de una unidad funcional posicionada en la planta."""
    unidad: "Unidad"
    x: float
    y: float
    ancho: float
    alto: float
    ambientes_geom: list[RectAmbiente] = field(default_factory=list)
    lado: str = "sur"   # "sur" o "norte"

    @property
    def cx(self) -> float:
        return self.x + self.ancho / 2

    @property
    def cy(self) -> float:
        return self.y + self.alto / 2


@dataclass
class GeometriaCore:
    """Posición y dimensiones del núcleo vertical (escaleras + ascensor)."""
    x: float
    y: float
    ancho: float
    alto: float

    @property
    def cx(self) -> float:
        return self.x + self.ancho / 2

    @property
    def cy(self) -> float:
        return self.y + self.alto / 2


@dataclass
class GeometriaPasillo:
    """Pasillo horizontal de distribución."""
    x: float
    y: float
    ancho: float    # largo del pasillo (en X)
    alto: float     # ancho del pasillo (en Y = ancho_pasillo_m)


@dataclass
class GeometriaPlanta:
    """
    Geometría 2D completa de una planta tipo.

    Sistema de coordenadas:
        Origen (0, 0) en esquina inferior-izquierda del polígono de planta.
        X: dirección frente del lote (0 → ancho_total).
        Y: dirección fondo del lote  (0 → fondo_total).
    """
    planta: "Planta"
    ancho_total: float          # W = frente - 2 * retiro_lateral
    fondo_total: float          # D = fondo  - retiro_frontal - retiro_posterior
    unidades: list[GeometriaUnidad]
    pasillo: GeometriaPasillo
    core: GeometriaCore
    dist_max_evacuacion_m: float


# ---------------------------------------------------------------------------
# Generador de planta
# ---------------------------------------------------------------------------

class GeneradorPlanta:
    """
    Genera el layout 2D de una planta tipo.

    Uso:
        gen = GeneradorPlanta()
        geom = gen.generar(planta, lote, edificio)
    """

    def generar(
        self,
        planta: "Planta",
        lote: "Lote",
        edificio: "Edificio",
    ) -> GeometriaPlanta:
        """
        Genera la geometría 2D de la planta indicada.

        Args:
            planta:   Planta a distribuir (unidades, núcleo, pasillo).
            lote:     Lote del proyecto (para dimensiones de huella).
            edificio: Edificio (para retiros).

        Returns:
            GeometriaPlanta con todas las entidades posicionadas.
        """
        W, D = self._dimensiones_planta(lote, edificio)
        core         = self._layout_core(planta, D)
        pasillo      = self._layout_pasillo(planta, core, W, D)
        unidades_geom = self._layout_unidades(planta, core, pasillo, W, D)
        dist_evac    = self._distancia_max_evacuacion(unidades_geom, core)

        return GeometriaPlanta(
            planta=planta,
            ancho_total=W,
            fondo_total=D,
            unidades=unidades_geom,
            pasillo=pasillo,
            core=core,
            dist_max_evacuacion_m=dist_evac,
        )

    # -----------------------------------------------------------------------
    # Helpers privados
    # -----------------------------------------------------------------------

    @staticmethod
    def _dimensiones_planta(lote: "Lote", edificio: "Edificio") -> tuple[float, float]:
        W = max(lote.frente_m - 2.0 * edificio.retiro_lateral_m, 5.0)
        D = max(lote.fondo_m - edificio.retiro_frontal_m - edificio.retiro_posterior_m, 8.0)
        return round(W, 3), round(D, 3)

    @staticmethod
    def _layout_core(planta: "Planta", D: float) -> GeometriaCore:
        n = planta.nucleo
        y_core = max(0.0, (D - n.largo_m) / 2)
        return GeometriaCore(x=0.0, y=y_core, ancho=n.ancho_m, alto=n.largo_m)

    @staticmethod
    def _layout_pasillo(
        planta: "Planta",
        core: GeometriaCore,
        W: float,
        D: float,
    ) -> GeometriaPasillo:
        p_alto  = planta.ancho_pasillo_m
        p_y     = max(0.0, (D - p_alto) / 2)
        p_x     = core.ancho
        p_ancho = max(W - core.ancho, 0.1)
        return GeometriaPasillo(x=p_x, y=p_y, ancho=p_ancho, alto=p_alto)

    def _layout_unidades(
        self,
        planta: "Planta",
        core: GeometriaCore,
        pasillo: GeometriaPasillo,
        W: float,
        D: float,
    ) -> list[GeometriaUnidad]:
        unidades = planta.unidades
        if not unidades:
            return []

        n       = len(unidades)
        n_sur   = (n + 1) // 2   # mitad superior (redondeo hacia arriba) → lado sur
        n_norte = n - n_sur

        x_ini    = core.ancho
        x_usable = max(W - core.ancho, 0.1)

        y_sur_ini    = 0.0
        y_sur_alto   = pasillo.y
        y_norte_ini  = pasillo.y + pasillo.alto
        y_norte_alto = D - y_norte_ini

        resultado: list[GeometriaUnidad] = []

        if n_sur > 0 and y_sur_alto > 0:
            w_u = x_usable / n_sur
            for i, u in enumerate(unidades[:n_sur]):
                x0 = x_ini + i * w_u
                resultado.append(
                    self._layout_unidad(u, x0, y_sur_ini, w_u, y_sur_alto, "sur")
                )

        if n_norte > 0 and y_norte_alto > 0:
            w_u = x_usable / n_norte
            for i, u in enumerate(unidades[n_sur:]):
                x0 = x_ini + i * w_u
                resultado.append(
                    self._layout_unidad(u, x0, y_norte_ini, w_u, y_norte_alto, "norte")
                )

        return resultado

    def _layout_unidad(
        self,
        unidad: "Unidad",
        x0: float,
        y0: float,
        ancho: float,
        alto: float,
        lado: str,
    ) -> GeometriaUnidad:
        """Distribuye los ambientes de una unidad dentro de su bounding box."""
        ambientes_geom = _distribuir_ambientes(unidad.ambientes, x0, y0, ancho, alto)
        return GeometriaUnidad(
            unidad=unidad,
            x=x0, y=y0,
            ancho=ancho, alto=alto,
            ambientes_geom=ambientes_geom,
            lado=lado,
        )

    @staticmethod
    def _distancia_max_evacuacion(
        unidades: list[GeometriaUnidad],
        core: GeometriaCore,
    ) -> float:
        """Distancia euclidiana máxima desde cualquier esquina de unidad al core."""
        if not unidades:
            return 0.0
        cx, cy  = core.cx, core.cy
        max_d   = 0.0
        for u in unidades:
            for px, py in [
                (u.x,           u.y),
                (u.x + u.ancho, u.y),
                (u.x,           u.y + u.alto),
                (u.x + u.ancho, u.y + u.alto),
            ]:
                d = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
                if d > max_d:
                    max_d = d
        return round(max_d, 2)


# ---------------------------------------------------------------------------
# Función auxiliar de distribución de ambientes
# ---------------------------------------------------------------------------

def _distribuir_ambientes(
    ambientes: list["Ambiente"],
    x0: float,
    y0: float,
    ancho: float,
    alto: float,
) -> list[RectAmbiente]:
    """
    Distribuye ambientes en zonas funcionales dentro del bounding box.

    Layout (de abajo hacia arriba):
        ┌──────────────────┐  ↑
        │     BALCÓN       │  h_bal
        ├────────┬─────────┤
        │ SOCIAL │ PRIVADO │  h_main
        ├────────┴─────────┤
        │    SERVICIOS     │  h_serv
        ├──────────────────┤
        │   CIRCULACIÓN    │  h_circ
        └──────────────────┘  ↓
    """
    if not ambientes or ancho <= 0 or alto <= 0:
        return []

    balcones  = [a for a in ambientes if a.tipo == TipoAmbiente.BALCON]
    sociales  = [a for a in ambientes if a.tipo in _ZONA_SOCIAL]
    privados  = [a for a in ambientes if a.tipo in _ZONA_PRIVADA]
    servicios = [a for a in ambientes if a.tipo in _ZONA_SERVICIO]
    circs     = [a for a in ambientes if a.tipo == TipoAmbiente.CIRCULACION_INTERNA]

    s_bal  = sum(a.superficie_m2 for a in balcones)
    s_soc  = sum(a.superficie_m2 for a in sociales)
    s_priv = sum(a.superficie_m2 for a in privados)
    s_serv = sum(a.superficie_m2 for a in servicios)
    s_circ = max(sum(a.superficie_m2 for a in circs), 1.0)
    s_total = max(s_bal + s_soc + s_priv + s_serv + s_circ, 1.0)

    h_circ = alto * (s_circ / s_total)
    h_serv = alto * (s_serv / s_total) if s_serv > 0 else 0.0
    h_main = alto * ((s_soc + s_priv) / s_total) if (s_soc + s_priv) > 0 else 0.0
    h_bal  = alto * (s_bal  / s_total) if s_bal  > 0 else 0.0

    y_circ = y0
    y_serv = y_circ + h_circ
    y_main = y_serv + h_serv
    y_bal  = y_main + h_main

    s_main = s_soc + s_priv
    w_soc  = ancho * (s_soc  / s_main) if s_main > 0 and s_soc  > 0 else 0.0
    w_priv = ancho * (s_priv / s_main) if s_main > 0 and s_priv > 0 else 0.0

    result: list[RectAmbiente] = []

    def franja(ams: list, x_ini: float, y_ini: float, w_total: float, h: float) -> None:
        if not ams or h <= 0 or w_total <= 0:
            return
        a_total = sum(a.superficie_m2 for a in ams) or 1.0
        cx = x_ini
        for a in ams:
            w = (a.superficie_m2 / a_total) * w_total
            result.append(RectAmbiente(ambiente=a, x=cx, y=y_ini, ancho=w, alto=h))
            cx += w

    def columna(ams: list, x_ini: float, y_ini: float, w: float, h_total: float) -> None:
        if not ams or w <= 0 or h_total <= 0:
            return
        a_total = sum(a.superficie_m2 for a in ams) or 1.0
        cy = y_ini
        for a in ams:
            h = (a.superficie_m2 / a_total) * h_total
            result.append(RectAmbiente(ambiente=a, x=x_ini, y=cy, ancho=w, alto=h))
            cy += h

    franja(circs,     x0,           y_circ, ancho,  h_circ)
    franja(servicios, x0,           y_serv, ancho,  h_serv)
    columna(sociales, x0,           y_main, w_soc,  h_main)
    columna(privados, x0 + w_soc,   y_main, w_priv, h_main)
    franja(balcones,  x0,           y_bal,  ancho,  h_bal)

    return result
