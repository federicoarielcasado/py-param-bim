"""
unidad.py
---------
Renderizador de planta esquemática 2D de una unidad funcional.

Vista asociada: SeccionActiva.TIPOLOGIAS

Genera un esquema proporcional de la planta del departamento distribuyendo
los ambientes en zonas funcionales:

  Distribución vertical (de abajo hacia arriba):
    ┌──────────────────────────────────────┐
    │              BALCÓN                  │  ← franja superior (si existe)
    ├─────────────────────┬────────────────┤
    │  SOCIAL             │  PRIVADO       │  ← zona principal
    │  (living, cocina,   │  (dormitorios) │
    │   estudio)          │                │
    ├─────────────────────┴────────────────┤
    │  SERVICIOS  (baños, toilette, lav.)  │  ← franja de servicio
    ├──────────────────────────────────────┤
    │           CIRCULACIÓN                │  ← franja inferior
    └──────────────────────────────────────┘

El MultiBlock retornado contiene:
    "habitaciones" → sub-MultiBlock con un PolyData por ambiente
    "etiquetas"    → PolyData con centroides de cada ambiente y:
                       point_data["tipo_int"] (int, mapa TIPO_A_INT)
                       point_data["area_m2"]  (float)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

try:
    import pyvista as pv
    import numpy as np
    PYVISTA_DISPONIBLE = True
except ImportError:
    PYVISTA_DISPONIBLE = False

from bim_generador.nucleo.motor_parametros import TipoAmbiente, TipoPlanta

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto, Unidad, Ambiente


# ---------------------------------------------------------------------------
# Mapeo TipoAmbiente → entero para cell_data
# (VTK solo admite caracteres ASCII en string arrays; usamos enteros)
# ---------------------------------------------------------------------------

TIPO_A_INT: dict[TipoAmbiente, int] = {
    TipoAmbiente.DORMITORIO_SIMPLE:    0,
    TipoAmbiente.DORMITORIO_PRINCIPAL: 1,
    TipoAmbiente.LIVING_COMEDOR:       2,
    TipoAmbiente.COCINA:               3,
    TipoAmbiente.BANIO:                4,
    TipoAmbiente.TOILETTE:             5,
    TipoAmbiente.LAVADERO:             6,
    TipoAmbiente.ESTUDIO:              7,
    TipoAmbiente.BALCON:               8,
    TipoAmbiente.CIRCULACION_INTERNA:  9,
}

# Clasificación por zona funcional
_ZONA_SOCIAL   = frozenset({
    TipoAmbiente.LIVING_COMEDOR,
    TipoAmbiente.COCINA,
    TipoAmbiente.ESTUDIO,
})
_ZONA_PRIVADA  = frozenset({
    TipoAmbiente.DORMITORIO_SIMPLE,
    TipoAmbiente.DORMITORIO_PRINCIPAL,
})
_ZONA_SERVICIO = frozenset({
    TipoAmbiente.BANIO,
    TipoAmbiente.TOILETTE,
    TipoAmbiente.LAVADERO,
})


class RenderizadorUnidad:
    """
    Renderizador de planta esquemática 2D de un departamento.

    Uso:
        render = RenderizadorUnidad()
        mb = render.renderizar(proyecto, contexto={"unidad_idx": 0})
        # mb["habitaciones"]  → MultiBlock con un PolyData por ambiente
        # mb["etiquetas"]     → PolyData con centroides y tipo_int/area_m2
    """

    def renderizar(
        self,
        proyecto: "Proyecto",
        contexto: Optional[dict] = None,
    ) -> "pv.MultiBlock | None":
        """
        Genera la planta esquemática de una unidad funcional.

        Args:
            proyecto: Proyecto actual.
            contexto: Diccionario opcional. Clave:
                "unidad_idx" (int) → índice de la unidad en la planta tipo.

        Retorna:
            pv.MultiBlock con "habitaciones" y "etiquetas",
            o None si pyvista no está disponible.
        """
        if not PYVISTA_DISPONIBLE:
            return None

        contexto = contexto or {}
        unidad = self._resolver_unidad(proyecto, contexto)

        if unidad is None or not unidad.ambientes:
            return self._bloque_vacio()

        return self._generar_schema(unidad)

    @staticmethod
    def tipo_vista() -> str:
        """Identificador del tipo de vista que genera este renderizador."""
        return "unidad_2d"

    # -----------------------------------------------------------------------
    # Selección de unidad
    # -----------------------------------------------------------------------

    def _resolver_unidad(
        self,
        proyecto: "Proyecto",
        contexto: dict,
    ) -> Optional["Unidad"]:
        """
        Selecciona la unidad a renderizar.
        Usa la primera planta tipo disponible (PLANTA_TIPO) o la primera planta.
        Si contexto["unidad_idx"] existe, selecciona esa unidad en esa planta.
        """
        plantas = proyecto.edificio.plantas
        if not plantas:
            return None

        planta_ref = next(
            (p for p in plantas if p.tipo_planta == TipoPlanta.PLANTA_TIPO),
            plantas[0],
        )
        if not planta_ref.unidades:
            return None

        idx = int(contexto.get("unidad_idx", 0))
        idx = max(0, min(idx, len(planta_ref.unidades) - 1))
        return planta_ref.unidades[idx]

    # -----------------------------------------------------------------------
    # Generación de geometría
    # -----------------------------------------------------------------------

    def _bloque_vacio(self) -> "pv.MultiBlock":
        bloque = pv.MultiBlock()
        bloque["habitaciones"] = pv.MultiBlock()
        bloque["etiquetas"]    = pv.PolyData()
        return bloque

    def _generar_schema(self, unidad: "Unidad") -> "pv.MultiBlock":
        """Genera la planta esquemática 2D de la unidad."""

        # Agrupar ambientes por zona funcional
        balcones  = [a for a in unidad.ambientes if a.tipo == TipoAmbiente.BALCON]
        sociales  = [a for a in unidad.ambientes if a.tipo in _ZONA_SOCIAL]
        privados  = [a for a in unidad.ambientes if a.tipo in _ZONA_PRIVADA]
        servicios = [a for a in unidad.ambientes if a.tipo in _ZONA_SERVICIO]
        circs     = [a for a in unidad.ambientes if a.tipo == TipoAmbiente.CIRCULACION_INTERNA]

        # Superficies por zona (circulación tiene mínimo 2 m² para visualización)
        s_balcon  = sum(a.superficie_m2 for a in balcones)
        s_social  = sum(a.superficie_m2 for a in sociales)
        s_privado = sum(a.superficie_m2 for a in privados)
        s_serv    = sum(a.superficie_m2 for a in servicios)
        s_circ    = max(sum(a.superficie_m2 for a in circs), 2.0)

        s_total = max(unidad.superficie_total_m2, 1.0)

        # Dimensiones generales del rectángulo de planta (aspecto ~ 1:1.3)
        ancho = math.sqrt(s_total / 1.3)
        if ancho <= 0:
            ancho = 1.0

        # Alturas proporcionales de cada franja (area_zona / ancho)
        h_circ   = s_circ   / ancho
        h_serv   = (s_serv   / ancho) if s_serv   > 0 else 0.0
        h_main   = ((s_social + s_privado) / ancho) if (s_social + s_privado) > 0 else 0.0
        h_balcon = (s_balcon / ancho) if s_balcon > 0 else 0.0

        # Anchos de columnas en la zona principal (proporcional a área)
        s_main = s_social + s_privado
        if s_main > 0:
            w_social  = ancho * (s_social  / s_main) if s_social  > 0 else 0.0
            w_privado = ancho * (s_privado / s_main) if s_privado > 0 else 0.0
        else:
            w_social  = ancho
            w_privado = 0.0

        # Posiciones Y absolutas de inicio de cada franja (origen en Y=0)
        y0_circ   = 0.0
        y0_serv   = h_circ
        y0_main   = y0_serv + h_serv
        y0_balcon = y0_main + h_main

        # Acumuladores de geometría y datos de etiquetas
        habitaciones: pv.MultiBlock = pv.MultiBlock()
        centroides:   list = []
        tipos_int:    list = []
        areas:        list = []

        # ---- Franja inferior: circulación -----------------------------------
        if circs and h_circ > 0:
            self._franja_horizontal(
                circs, 0.0, ancho, y0_circ, h_circ,
                habitaciones, centroides, tipos_int, areas,
            )

        # ---- Franja de servicios: baños, toilette, lavadero ----------------
        if servicios and h_serv > 0:
            self._franja_horizontal(
                servicios, 0.0, ancho, y0_serv, h_serv,
                habitaciones, centroides, tipos_int, areas,
            )

        # ---- Zona principal — columna social (izquierda) -------------------
        if sociales and h_main > 0 and w_social > 0:
            self._columna_vertical(
                sociales, 0.0, w_social, y0_main, h_main,
                habitaciones, centroides, tipos_int, areas,
            )

        # ---- Zona principal — columna privada (derecha) --------------------
        if privados and h_main > 0 and w_privado > 0:
            self._columna_vertical(
                privados, w_social, ancho, y0_main, h_main,
                habitaciones, centroides, tipos_int, areas,
            )

        # ---- Franja superior: balcón ----------------------------------------
        if balcones and h_balcon > 0:
            self._franja_horizontal(
                balcones, 0.0, ancho, y0_balcon, h_balcon,
                habitaciones, centroides, tipos_int, areas,
            )

        # ---- PolyData de etiquetas (centroides con metadatos) ---------------
        etiquetas = pv.PolyData()
        if centroides:
            etiquetas.points      = np.array(centroides, dtype=float)
            etiquetas["tipo_int"] = np.array(tipos_int,  dtype=int)
            etiquetas["area_m2"]  = np.array(areas,       dtype=float)

        bloques = pv.MultiBlock()
        bloques["habitaciones"] = habitaciones
        bloques["etiquetas"]    = etiquetas
        return bloques

    # -----------------------------------------------------------------------
    # Helpers de posicionado
    # -----------------------------------------------------------------------

    @staticmethod
    def _rect(x0: float, x1: float, y0: float, y1: float, z: float = 0.0) -> "pv.PolyData":
        """Genera un rectángulo relleno como pv.PolyData."""
        puntos = np.array([
            [x0, y0, z],
            [x1, y0, z],
            [x1, y1, z],
            [x0, y1, z],
        ], dtype=float)
        caras = np.array([4, 0, 1, 2, 3])
        return pv.PolyData(puntos, caras)

    def _agregar_ambiente(
        self,
        ambiente: "Ambiente",
        x0: float, x1: float,
        y0: float, y1: float,
        habitaciones: "pv.MultiBlock",
        centroides: list, tipos_int: list, areas: list,
    ) -> None:
        """Genera el mesh de un ambiente y lo agrega a los acumuladores."""
        mesh     = self._rect(x0, x1, y0, y1)
        tipo_int = TIPO_A_INT.get(ambiente.tipo, 9)
        mesh.cell_data["tipo_int"] = [tipo_int]
        mesh.cell_data["area_m2"]  = [round(ambiente.superficie_m2, 2)]

        nombre_clave = f"amb_{len(habitaciones)}"
        habitaciones[nombre_clave] = mesh

        centroides.append([(x0 + x1) / 2, (y0 + y1) / 2, 0.02])
        tipos_int.append(tipo_int)
        areas.append(round(ambiente.superficie_m2, 2))

    def _franja_horizontal(
        self,
        ambientes: list,
        x_ini: float, x_fin: float,
        y_ini: float, alto: float,
        habitaciones: "pv.MultiBlock",
        centroides: list, tipos_int: list, areas: list,
    ) -> None:
        """
        Coloca ambientes en una franja horizontal.
        Cada ambiente recibe un ancho proporcional a su área.
        """
        if not ambientes or alto <= 0:
            return
        ancho_total = x_fin - x_ini
        area_total  = sum(a.superficie_m2 for a in ambientes) or 1.0
        x_cursor    = x_ini
        for amb in ambientes:
            w = (amb.superficie_m2 / area_total) * ancho_total
            self._agregar_ambiente(
                amb, x_cursor, x_cursor + w, y_ini, y_ini + alto,
                habitaciones, centroides, tipos_int, areas,
            )
            x_cursor += w

    def _columna_vertical(
        self,
        ambientes: list,
        x_ini: float, x_fin: float,
        y_ini: float, alto_total: float,
        habitaciones: "pv.MultiBlock",
        centroides: list, tipos_int: list, areas: list,
    ) -> None:
        """
        Coloca ambientes en una columna vertical.
        Cada ambiente recibe una altura proporcional a su área.
        """
        if not ambientes or alto_total <= 0:
            return
        area_total = sum(a.superficie_m2 for a in ambientes) or 1.0
        y_cursor   = y_ini
        for amb in ambientes:
            h = (amb.superficie_m2 / area_total) * alto_total
            self._agregar_ambiente(
                amb, x_ini, x_fin, y_cursor, y_cursor + h,
                habitaciones, centroides, tipos_int, areas,
            )
            y_cursor += h
