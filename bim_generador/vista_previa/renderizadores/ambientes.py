"""
ambientes.py
------------
Renderizador de planta 2D con ambiente seleccionado resaltado.

Vista asociada: SeccionActiva.AMBIENTES

Genera la misma planta esquemática que RenderizadorUnidad pero aplica
diferenciación visual entre el ambiente activo (resaltado) y el resto
(atenuados), para guiar la edición de propiedades en PanelAmbientes.

El MultiBlock retornado contiene:
    "habitaciones_amb" → sub-MultiBlock con un PolyData por ambiente, con:
                           cell_data["tipo_int"]         (int, mapa TIPO_A_INT)
                           cell_data["area_m2"]           (float)
                           cell_data["seleccionado"]      (0 = atenuado, 1 = resaltado)
                           cell_data["ambiente_orig_idx"] (int, posición en unidad.ambientes)
    "etiquetas"        → PolyData con centroides y:
                           point_data["tipo_int"]
                           point_data["area_m2"]
                           point_data["seleccionado"]

Contexto esperado:
    {"unidad_idx": N, "ambiente_idx": M}
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
from bim_generador.vista_previa.renderizadores.unidad import TIPO_A_INT, _ZONA_SOCIAL, _ZONA_PRIVADA, _ZONA_SERVICIO

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto, Unidad, Ambiente


class RenderizadorAmbientes:
    """
    Renderizador de planta 2D con un ambiente resaltado.

    Uso:
        render = RenderizadorAmbientes()
        mb = render.renderizar(proyecto, contexto={"unidad_idx": 0, "ambiente_idx": 2})
        # mb["habitaciones_amb"] → MultiBlock, cada mesh tiene cell_data["seleccionado"]
        # mb["etiquetas"]        → PolyData con centroides y metadatos
    """

    def renderizar(
        self,
        proyecto: "Proyecto",
        contexto: Optional[dict] = None,
    ) -> "pv.MultiBlock | None":
        if not PYVISTA_DISPONIBLE:
            return None

        contexto = contexto or {}
        unidad = self._resolver_unidad(proyecto, contexto)

        if unidad is None or not unidad.ambientes:
            return self._bloque_vacio()

        ambiente_idx = int(contexto.get("ambiente_idx", 0))
        ambiente_idx = max(0, min(ambiente_idx, len(unidad.ambientes) - 1))

        return self._generar_schema(unidad, ambiente_idx)

    @staticmethod
    def tipo_vista() -> str:
        return "ambientes_2d"

    # -----------------------------------------------------------------------
    # Selección de unidad
    # -----------------------------------------------------------------------

    def _resolver_unidad(
        self,
        proyecto: "Proyecto",
        contexto: dict,
    ) -> Optional["Unidad"]:
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
        bloque["habitaciones_amb"] = pv.MultiBlock()
        bloque["etiquetas"]        = pv.PolyData()
        return bloque

    def _generar_schema(self, unidad: "Unidad", ambiente_idx: int) -> "pv.MultiBlock":
        """Genera la planta con la unidad completa y el ambiente indicado resaltado."""

        # Agrupar ambientes como (orig_idx, ambiente) para rastrear índice original
        todos = list(enumerate(unidad.ambientes))
        balcones  = [(i, a) for i, a in todos if a.tipo == TipoAmbiente.BALCON]
        sociales  = [(i, a) for i, a in todos if a.tipo in _ZONA_SOCIAL]
        privados  = [(i, a) for i, a in todos if a.tipo in _ZONA_PRIVADA]
        servicios = [(i, a) for i, a in todos if a.tipo in _ZONA_SERVICIO]
        circs     = [(i, a) for i, a in todos if a.tipo == TipoAmbiente.CIRCULACION_INTERNA]

        s_balcon  = sum(a.superficie_m2 for _, a in balcones)
        s_social  = sum(a.superficie_m2 for _, a in sociales)
        s_privado = sum(a.superficie_m2 for _, a in privados)
        s_serv    = sum(a.superficie_m2 for _, a in servicios)
        s_circ    = max(sum(a.superficie_m2 for _, a in circs), 2.0)

        s_total = max(unidad.superficie_total_m2, 1.0)

        ancho = math.sqrt(s_total / 1.3)
        if ancho <= 0:
            ancho = 1.0

        h_circ   = s_circ   / ancho
        h_serv   = (s_serv   / ancho) if s_serv   > 0 else 0.0
        h_main   = ((s_social + s_privado) / ancho) if (s_social + s_privado) > 0 else 0.0
        h_balcon = (s_balcon / ancho) if s_balcon > 0 else 0.0

        s_main = s_social + s_privado
        if s_main > 0:
            w_social  = ancho * (s_social  / s_main) if s_social  > 0 else 0.0
            w_privado = ancho * (s_privado / s_main) if s_privado > 0 else 0.0
        else:
            w_social  = ancho
            w_privado = 0.0

        y0_circ   = 0.0
        y0_serv   = h_circ
        y0_main   = y0_serv + h_serv
        y0_balcon = y0_main + h_main

        habitaciones: pv.MultiBlock = pv.MultiBlock()
        centroides:   list = []
        tipos_int:    list = []
        areas:        list = []
        seleccionados: list = []

        if circs and h_circ > 0:
            self._franja_horizontal(
                circs, 0.0, ancho, y0_circ, h_circ, ambiente_idx,
                habitaciones, centroides, tipos_int, areas, seleccionados,
            )
        if servicios and h_serv > 0:
            self._franja_horizontal(
                servicios, 0.0, ancho, y0_serv, h_serv, ambiente_idx,
                habitaciones, centroides, tipos_int, areas, seleccionados,
            )
        if sociales and h_main > 0 and w_social > 0:
            self._columna_vertical(
                sociales, 0.0, w_social, y0_main, h_main, ambiente_idx,
                habitaciones, centroides, tipos_int, areas, seleccionados,
            )
        if privados and h_main > 0 and w_privado > 0:
            self._columna_vertical(
                privados, w_social, ancho, y0_main, h_main, ambiente_idx,
                habitaciones, centroides, tipos_int, areas, seleccionados,
            )
        if balcones and h_balcon > 0:
            self._franja_horizontal(
                balcones, 0.0, ancho, y0_balcon, h_balcon, ambiente_idx,
                habitaciones, centroides, tipos_int, areas, seleccionados,
            )

        etiquetas = pv.PolyData()
        if centroides:
            etiquetas.points           = np.array(centroides,   dtype=float)
            etiquetas["tipo_int"]      = np.array(tipos_int,    dtype=int)
            etiquetas["area_m2"]       = np.array(areas,         dtype=float)
            etiquetas["seleccionado"]  = np.array(seleccionados, dtype=int)

        bloques = pv.MultiBlock()
        bloques["habitaciones_amb"] = habitaciones
        bloques["etiquetas"]        = etiquetas
        return bloques

    # -----------------------------------------------------------------------
    # Helpers de posicionado (con rastreo de índice original)
    # -----------------------------------------------------------------------

    @staticmethod
    def _rect(x0: float, x1: float, y0: float, y1: float, z: float = 0.0) -> "pv.PolyData":
        puntos = np.array([
            [x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z],
        ], dtype=float)
        return pv.PolyData(puntos, np.array([4, 0, 1, 2, 3]))

    def _agregar_amb(
        self,
        orig_idx: int,
        ambiente: "Ambiente",
        x0: float, x1: float,
        y0: float, y1: float,
        seleccionado_idx: int,
        habitaciones: "pv.MultiBlock",
        centroides: list, tipos_int: list, areas: list, seleccionados: list,
    ) -> None:
        mesh     = self._rect(x0, x1, y0, y1)
        tipo_int = TIPO_A_INT.get(ambiente.tipo, 9)
        es_sel   = 1 if orig_idx == seleccionado_idx else 0

        mesh.cell_data["tipo_int"]          = [tipo_int]
        mesh.cell_data["area_m2"]           = [round(ambiente.superficie_m2, 2)]
        mesh.cell_data["seleccionado"]      = [es_sel]
        mesh.cell_data["ambiente_orig_idx"] = [orig_idx]

        habitaciones[f"amb_{len(habitaciones)}"] = mesh

        centroides.append([(x0 + x1) / 2, (y0 + y1) / 2, 0.02])
        tipos_int.append(tipo_int)
        areas.append(round(ambiente.superficie_m2, 2))
        seleccionados.append(es_sel)

    def _franja_horizontal(
        self,
        pares: list,
        x_ini: float, x_fin: float,
        y_ini: float, alto: float,
        seleccionado_idx: int,
        habitaciones: "pv.MultiBlock",
        centroides: list, tipos_int: list, areas: list, seleccionados: list,
    ) -> None:
        if not pares or alto <= 0:
            return
        ancho_total = x_fin - x_ini
        area_total  = sum(a.superficie_m2 for _, a in pares) or 1.0
        x_cursor    = x_ini
        for orig_idx, amb in pares:
            w = (amb.superficie_m2 / area_total) * ancho_total
            self._agregar_amb(
                orig_idx, amb, x_cursor, x_cursor + w, y_ini, y_ini + alto,
                seleccionado_idx, habitaciones, centroides, tipos_int, areas, seleccionados,
            )
            x_cursor += w

    def _columna_vertical(
        self,
        pares: list,
        x_ini: float, x_fin: float,
        y_ini: float, alto_total: float,
        seleccionado_idx: int,
        habitaciones: "pv.MultiBlock",
        centroides: list, tipos_int: list, areas: list, seleccionados: list,
    ) -> None:
        if not pares or alto_total <= 0:
            return
        area_total = sum(a.superficie_m2 for _, a in pares) or 1.0
        y_cursor   = y_ini
        for orig_idx, amb in pares:
            h = (amb.superficie_m2 / area_total) * alto_total
            self._agregar_amb(
                orig_idx, amb, x_ini, x_fin, y_cursor, y_cursor + h,
                seleccionado_idx, habitaciones, centroides, tipos_int, areas, seleccionados,
            )
            y_cursor += h
