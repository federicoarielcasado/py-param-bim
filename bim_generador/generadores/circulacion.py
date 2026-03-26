"""
circulacion.py
--------------
Generador de núcleos de circulación vertical y pasillos.

Calcula métricas de circulación a partir de la geometría de planta
generada por GeneradorPlanta.

Sprint 6: implementación completa.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from bim_generador.generadores.planta import GeneradorPlanta, GeometriaPlanta

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Edificio


class GeneradorCirculacion:
    """Genera métricas de circulación vertical y horizontal."""

    def generar_nucleos(self, edificio: "Edificio") -> list[dict]:
        """
        Retorna la posición del núcleo vertical para cada planta del edificio.

        Returns:
            Lista de dicts con: planta_numero, planta_nombre, x, y, ancho, largo,
            tiene_ascensor, cantidad_escaleras.
        """
        resultado = []
        for planta in edificio.plantas:
            n = planta.nucleo
            resultado.append({
                "planta_numero":       planta.numero,
                "planta_nombre":       planta.nombre,
                "x":                   0.0,
                "y":                   0.0,
                "ancho":               n.ancho_m,
                "largo":               n.largo_m,
                "tiene_ascensor":      n.tiene_ascensor,
                "cantidad_escaleras":  n.cantidad_escaleras,
            })
        return resultado

    def calcular_distancia_evacuacion(self, geom_planta: GeometriaPlanta) -> float:
        """
        Retorna la distancia máxima de evacuación ya calculada en la geometría.

        Args:
            geom_planta: GeometriaPlanta generada por GeneradorPlanta.

        Returns:
            Distancia en metros.
        """
        return geom_planta.dist_max_evacuacion_m

    def metricas_planta(self, geom_planta: GeometriaPlanta) -> dict:
        """
        Calcula métricas de circulación para una planta.

        Returns:
            Dict con: dist_max_evacuacion_m, ancho_pasillo_m, sup_pasillo_m2,
            sup_core_m2, ratio_circulacion, cantidad_unidades.
        """
        planta      = geom_planta.planta
        sup_pasillo = geom_planta.pasillo.ancho * geom_planta.pasillo.alto
        sup_core    = geom_planta.core.ancho    * geom_planta.core.alto
        sup_total   = geom_planta.ancho_total   * geom_planta.fondo_total

        ratio_circulacion = (
            (sup_pasillo + sup_core) / sup_total if sup_total > 0 else 0.0
        )

        return {
            "dist_max_evacuacion_m": geom_planta.dist_max_evacuacion_m,
            "ancho_pasillo_m":       planta.ancho_pasillo_m,
            "sup_pasillo_m2":        round(sup_pasillo, 2),
            "sup_core_m2":           round(sup_core, 2),
            "ratio_circulacion":     round(ratio_circulacion, 3),
            "cantidad_unidades":     planta.cantidad_unidades,
        }
