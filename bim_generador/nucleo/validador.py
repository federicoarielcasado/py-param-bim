"""
validador.py
------------
Validador normativo con soporte de perfiles por país/ciudad.

Carga el perfil normativo desde configuracion/normas/<perfil>.json y verifica
que el proyecto cumpla con las restricciones reglamentarias.

Estado: STUB parcial — implementación planificada para Sprint 5-6 (Fase 2).
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bim_generador.nucleo.motor_parametros import Proyecto

# Ruta base de perfiles normativos
DIR_NORMAS = Path(__file__).parent.parent / "configuracion" / "normas"


class ResultadoValidacion:
    """Resultado de una validación individual."""

    def __init__(self, regla: str, cumple: bool, mensaje: str,
                 valor_real: float | None = None, valor_limite: float | None = None):
        self.regla = regla
        self.cumple = cumple
        self.mensaje = mensaje
        self.valor_real = valor_real
        self.valor_limite = valor_limite

    def __repr__(self) -> str:
        estado = "✅" if self.cumple else "❌"
        return f"{estado} [{self.regla}] {self.mensaje}"


class Validador:
    """
    Validador normativo parametrizable por perfil de país/ciudad.

    Uso:
        validador = Validador("argentina_caba")
        resultados = validador.validar(proyecto)
    """

    def __init__(self, perfil: str = "argentina_caba"):
        self.perfil = perfil
        self.norma = self._cargar_norma(perfil)

    def _cargar_norma(self, perfil: str) -> dict:
        """Carga el archivo JSON del perfil normativo."""
        ruta = DIR_NORMAS / f"{perfil}.json"
        if not ruta.exists():
            raise FileNotFoundError(f"Perfil normativo no encontrado: {ruta}")
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)

    def validar(self, proyecto: "Proyecto") -> list[ResultadoValidacion]:
        """
        Ejecuta todas las reglas sobre el proyecto.

        Retorna:
            Lista de ResultadoValidacion con el estado de cada regla.
        """
        resultados: list[ResultadoValidacion] = []

        resultados.extend(self._validar_fos(proyecto))
        resultados.extend(self._validar_fot(proyecto))
        resultados.extend(self._validar_superficies_ambientes(proyecto))

        return resultados

    # ---- Reglas individuales -----------------------------------------------

    def _validar_fos(self, proyecto: "Proyecto") -> list[ResultadoValidacion]:
        fos_real  = proyecto.calcular_fos_real()
        fos_max   = self.norma.get("uso_suelo", {}).get("fos_max",
                    self.norma.get("fos_max", proyecto.lote.fos_max))
        cumple    = fos_real <= fos_max
        return [ResultadoValidacion(
            regla="FOS",
            cumple=cumple,
            mensaje=f"FOS real {fos_real:.2f} {'≤' if cumple else '>'} máximo {fos_max:.2f}",
            valor_real=fos_real,
            valor_limite=fos_max,
        )]

    def _validar_fot(self, proyecto: "Proyecto") -> list[ResultadoValidacion]:
        fot_real = proyecto.calcular_fot_real()
        fot_max  = self.norma.get("uso_suelo", {}).get("fot_max",
                   self.norma.get("fot_max", proyecto.lote.fot_max))
        cumple   = fot_real <= fot_max
        return [ResultadoValidacion(
            regla="FOT",
            cumple=cumple,
            mensaje=f"FOT real {fot_real:.2f} {'≤' if cumple else '>'} máximo {fot_max:.2f}",
            valor_real=fot_real,
            valor_limite=fot_max,
        )]

    def _validar_superficies_ambientes(self, proyecto: "Proyecto") -> list[ResultadoValidacion]:
        """Verifica superficies mínimas por tipo de ambiente."""
        min_areas: dict = self.norma.get("min_room_areas", {})
        resultados = []
        for planta in proyecto.edificio.plantas:
            for unidad in planta.unidades:
                for ambiente in unidad.ambientes:
                    clave = ambiente.tipo.value
                    if clave in min_areas:
                        minimo = min_areas[clave]
                        cumple = ambiente.superficie_m2 >= minimo
                        resultados.append(ResultadoValidacion(
                            regla=f"sup_min.{clave}",
                            cumple=cumple,
                            mensaje=(
                                f"[{planta.nombre} / Unidad {unidad.codigo}] "
                                f"{ambiente.nombre}: {ambiente.superficie_m2} m² "
                                f"{'≥' if cumple else '<'} mínimo {minimo} m²"
                            ),
                            valor_real=ambiente.superficie_m2,
                            valor_limite=minimo,
                        ))
        return resultados
