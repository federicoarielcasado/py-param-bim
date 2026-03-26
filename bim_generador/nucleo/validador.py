"""
validador.py
------------
Validador normativo con soporte de perfiles por país/ciudad.

Carga el perfil normativo desde configuracion/normas/<perfil>.json y verifica
que el proyecto cumpla con las restricciones reglamentarias.

Reglas implementadas (Sprint 6 — Fase 2 completo):
    FOS               — Factor de Ocupación del Suelo
    FOT               — Factor de Ocupación Total
    sup_min           — Superficies mínimas por tipo de ambiente
    dim_min           — Dimensión mínima (ancho) por tipo de ambiente
    ilum_vent         — Iluminación y ventilación natural en ambientes habitables
    sup_unidad        — Superficie total mínima por tipología de unidad
    ancho_pasillo     — Ancho de pasillo de distribución
    altura_libre      — Altura libre por piso
    evacuacion        — Distancia máxima de evacuación al núcleo vertical
    retiros           — Retiros mínimos del edificio
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

    def __init__(
        self,
        regla: str,
        cumple: bool,
        mensaje: str,
        valor_real: float | None = None,
        valor_limite: float | None = None,
    ):
        self.regla       = regla
        self.cumple      = cumple
        self.mensaje     = mensaje
        self.valor_real  = valor_real
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
        incumplimientos = [r for r in resultados if not r.cumple]
    """

    def __init__(self, perfil: str = "argentina_caba"):
        self.perfil = perfil
        self.norma  = self._cargar_norma(perfil)

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

        # Urbanísticas
        resultados.extend(self._validar_fos(proyecto))
        resultados.extend(self._validar_fot(proyecto))
        resultados.extend(self._validar_retiros(proyecto))

        # Ambientes
        resultados.extend(self._validar_superficies_ambientes(proyecto))
        resultados.extend(self._validar_dimensiones_ambientes(proyecto))
        resultados.extend(self._validar_iluminacion_ventilacion(proyecto))

        # Unidades
        resultados.extend(self._validar_superficie_unidad(proyecto))

        # Circulación y alturas
        resultados.extend(self._validar_ancho_pasillo(proyecto))
        resultados.extend(self._validar_altura_libre(proyecto))
        resultados.extend(self._validar_evacuacion(proyecto))

        return resultados

    # -----------------------------------------------------------------------
    # Reglas urbanísticas
    # -----------------------------------------------------------------------

    def _validar_fos(self, proyecto: "Proyecto") -> list[ResultadoValidacion]:
        fos_real = proyecto.calcular_fos_real()
        fos_max  = self.norma.get("uso_suelo", {}).get(
            "fos_max", proyecto.lote.fos_max
        )
        cumple = fos_real <= fos_max
        return [ResultadoValidacion(
            regla="FOS",
            cumple=cumple,
            mensaje=(
                f"FOS real {fos_real:.3f} "
                f"{'≤' if cumple else '>'} máximo {fos_max:.2f}"
            ),
            valor_real=fos_real,
            valor_limite=fos_max,
        )]

    def _validar_fot(self, proyecto: "Proyecto") -> list[ResultadoValidacion]:
        fot_real = proyecto.calcular_fot_real()
        fot_max  = self.norma.get("uso_suelo", {}).get(
            "fot_max", proyecto.lote.fot_max
        )
        cumple = fot_real <= fot_max
        return [ResultadoValidacion(
            regla="FOT",
            cumple=cumple,
            mensaje=(
                f"FOT real {fot_real:.3f} "
                f"{'≤' if cumple else '>'} máximo {fot_max:.2f}"
            ),
            valor_real=fot_real,
            valor_limite=fot_max,
        )]

    def _validar_retiros(self, proyecto: "Proyecto") -> list[ResultadoValidacion]:
        """Verifica que los retiros del edificio respeten los mínimos normativos."""
        retiros_norma: dict = self.norma.get("retiros_minimos_m", {})
        ed = proyecto.edificio
        pares = [
            ("retiro.frontal",    ed.retiro_frontal_m,   retiros_norma.get("frontal",   0.0)),
            ("retiro.lateral",    ed.retiro_lateral_m,   retiros_norma.get("lateral",   0.0)),
            ("retiro.posterior",  ed.retiro_posterior_m, retiros_norma.get("posterior", 0.0)),
        ]
        resultados = []
        for regla, valor, minimo in pares:
            if minimo <= 0:
                continue
            cumple = valor >= minimo
            nombre = regla.split(".")[1].title()
            resultados.append(ResultadoValidacion(
                regla=regla,
                cumple=cumple,
                mensaje=(
                    f"Retiro {nombre} {valor:.2f} m "
                    f"{'≥' if cumple else '<'} mínimo {minimo:.2f} m"
                ),
                valor_real=valor,
                valor_limite=minimo,
            ))
        return resultados

    # -----------------------------------------------------------------------
    # Reglas de ambientes
    # -----------------------------------------------------------------------

    def _validar_superficies_ambientes(
        self, proyecto: "Proyecto"
    ) -> list[ResultadoValidacion]:
        """Verifica superficies mínimas por tipo de ambiente."""
        min_areas: dict = self.norma.get("min_room_areas", {})
        resultados = []
        for planta in proyecto.edificio.plantas:
            for unidad in planta.unidades:
                for ambiente in unidad.ambientes:
                    clave = ambiente.tipo.value
                    if clave not in min_areas:
                        continue
                    minimo = min_areas[clave]
                    cumple = ambiente.superficie_m2 >= minimo
                    resultados.append(ResultadoValidacion(
                        regla=f"sup_min.{clave}",
                        cumple=cumple,
                        mensaje=(
                            f"[{planta.nombre} / Unidad {unidad.codigo}] "
                            f"{ambiente.nombre}: {ambiente.superficie_m2:.1f} m² "
                            f"{'≥' if cumple else '<'} mínimo {minimo:.1f} m²"
                        ),
                        valor_real=ambiente.superficie_m2,
                        valor_limite=minimo,
                    ))
        return resultados

    def _validar_dimensiones_ambientes(
        self, proyecto: "Proyecto"
    ) -> list[ResultadoValidacion]:
        """Verifica el ancho libre mínimo por tipo de ambiente."""
        min_dims: dict = self.norma.get("min_room_dimensions_m", {})
        resultados = []
        # Solo primera planta tipo para evitar duplicar mensajes idénticos
        planta_ref = next(
            (p for p in proyecto.edificio.plantas
             if p.tipo_planta.value == "planta_tipo"),
            proyecto.edificio.plantas[0] if proyecto.edificio.plantas else None,
        )
        if planta_ref is None:
            return resultados
        for unidad in planta_ref.unidades:
            for ambiente in unidad.ambientes:
                clave = ambiente.tipo.value
                if clave not in min_dims:
                    continue
                minimo = min_dims[clave]
                cumple = ambiente.ancho_min_m >= minimo
                resultados.append(ResultadoValidacion(
                    regla=f"dim_min.{clave}",
                    cumple=cumple,
                    mensaje=(
                        f"[Unidad {unidad.codigo}] {ambiente.nombre}: "
                        f"ancho {ambiente.ancho_min_m:.2f} m "
                        f"{'≥' if cumple else '<'} mínimo {minimo:.2f} m"
                    ),
                    valor_real=ambiente.ancho_min_m,
                    valor_limite=minimo,
                ))
        return resultados

    def _validar_iluminacion_ventilacion(
        self, proyecto: "Proyecto"
    ) -> list[ResultadoValidacion]:
        """
        Verifica que los ambientes habitables tengan iluminación y
        ventilación natural habilitadas.
        """
        iv_norma = self.norma.get("iluminacion_ventilacion", {})
        habitables: set[str] = set(iv_norma.get("ambientes_habitables", []))
        if not habitables:
            return []

        resultados = []
        # Solo planta tipo de referencia
        planta_ref = next(
            (p for p in proyecto.edificio.plantas
             if p.tipo_planta.value == "planta_tipo"),
            proyecto.edificio.plantas[0] if proyecto.edificio.plantas else None,
        )
        if planta_ref is None:
            return resultados

        for unidad in planta_ref.unidades:
            for ambiente in unidad.ambientes:
                if ambiente.tipo.value not in habitables:
                    continue

                if not ambiente.iluminacion_natural:
                    resultados.append(ResultadoValidacion(
                        regla="ilum_vent.iluminacion",
                        cumple=False,
                        mensaje=(
                            f"[Unidad {unidad.codigo}] {ambiente.nombre}: "
                            "sin iluminación natural (ambiente habitable)"
                        ),
                    ))
                else:
                    resultados.append(ResultadoValidacion(
                        regla="ilum_vent.iluminacion",
                        cumple=True,
                        mensaje=(
                            f"[Unidad {unidad.codigo}] {ambiente.nombre}: "
                            "iluminación natural ✓"
                        ),
                    ))

                if not ambiente.ventilacion_natural:
                    resultados.append(ResultadoValidacion(
                        regla="ilum_vent.ventilacion",
                        cumple=False,
                        mensaje=(
                            f"[Unidad {unidad.codigo}] {ambiente.nombre}: "
                            "sin ventilación natural (ambiente habitable)"
                        ),
                    ))
                else:
                    resultados.append(ResultadoValidacion(
                        regla="ilum_vent.ventilacion",
                        cumple=True,
                        mensaje=(
                            f"[Unidad {unidad.codigo}] {ambiente.nombre}: "
                            "ventilación natural ✓"
                        ),
                    ))

        return resultados

    # -----------------------------------------------------------------------
    # Reglas de unidades
    # -----------------------------------------------------------------------

    def _validar_superficie_unidad(
        self, proyecto: "Proyecto"
    ) -> list[ResultadoValidacion]:
        """Verifica la superficie total mínima por tipología de unidad."""
        tip_min: dict = self.norma.get("tipologias_minimas", {})
        if not tip_min:
            return []

        resultados = []
        planta_ref = next(
            (p for p in proyecto.edificio.plantas
             if p.tipo_planta.value == "planta_tipo"),
            proyecto.edificio.plantas[0] if proyecto.edificio.plantas else None,
        )
        if planta_ref is None:
            return resultados

        for unidad in planta_ref.unidades:
            clave = unidad.tipologia.value
            if clave not in tip_min:
                continue
            minimo = tip_min[clave]
            sup    = unidad.superficie_total_m2
            cumple = sup >= minimo
            resultados.append(ResultadoValidacion(
                regla=f"sup_unidad.{clave}",
                cumple=cumple,
                mensaje=(
                    f"[Unidad {unidad.codigo}] Tipología {clave}: "
                    f"{sup:.1f} m² "
                    f"{'≥' if cumple else '<'} mínimo {minimo:.1f} m²"
                ),
                valor_real=sup,
                valor_limite=minimo,
            ))
        return resultados

    # -----------------------------------------------------------------------
    # Reglas de circulación y altura
    # -----------------------------------------------------------------------

    def _validar_ancho_pasillo(
        self, proyecto: "Proyecto"
    ) -> list[ResultadoValidacion]:
        """Verifica que el ancho de pasillo cumpla el mínimo normativo."""
        circ = self.norma.get("circulacion", {})
        min_ancho = circ.get("ancho_pasillo_min_m", 1.20)
        resultados = []
        # Verifica todas las plantas (pueden tener distintos anchos)
        plantas_vistas: set[float] = set()
        for planta in proyecto.edificio.plantas:
            ancho = planta.ancho_pasillo_m
            if ancho in plantas_vistas:
                continue
            plantas_vistas.add(ancho)
            cumple = ancho >= min_ancho
            resultados.append(ResultadoValidacion(
                regla="ancho_pasillo",
                cumple=cumple,
                mensaje=(
                    f"Pasillo {ancho:.2f} m "
                    f"{'≥' if cumple else '<'} mínimo {min_ancho:.2f} m"
                ),
                valor_real=ancho,
                valor_limite=min_ancho,
            ))
        return resultados

    def _validar_altura_libre(
        self, proyecto: "Proyecto"
    ) -> list[ResultadoValidacion]:
        """Verifica la altura libre mínima por piso."""
        est_norma  = self.norma.get("estructura", {})
        circ_norma = self.norma.get("circulacion", {})
        min_altura = max(
            est_norma.get("altura_libre_minima_m",  2.40),
            circ_norma.get("altura_libre_min_m", 2.40),
        )
        resultados = []
        alturas_vistas: set[float] = set()
        for planta in proyecto.edificio.plantas:
            h = planta.altura_libre_m
            if h in alturas_vistas:
                continue
            alturas_vistas.add(h)
            cumple = h >= min_altura
            resultados.append(ResultadoValidacion(
                regla="altura_libre",
                cumple=cumple,
                mensaje=(
                    f"[{planta.nombre}] Altura libre {h:.2f} m "
                    f"{'≥' if cumple else '<'} mínimo {min_altura:.2f} m"
                ),
                valor_real=h,
                valor_limite=min_altura,
            ))
        return resultados

    def _validar_evacuacion(
        self, proyecto: "Proyecto"
    ) -> list[ResultadoValidacion]:
        """
        Verifica la distancia máxima de evacuación al núcleo vertical.
        Usa GeneradorPlanta para calcular la geometría real de cada planta.
        """
        from bim_generador.generadores.planta import GeneradorPlanta

        circ = self.norma.get("circulacion", {})
        max_evac = circ.get("max_distancia_evacuacion_m", 40.0)

        gen = GeneradorPlanta()
        resultados = []
        for planta in proyecto.edificio.plantas:
            if not planta.unidades:
                continue
            geom   = gen.generar(planta, proyecto.lote, proyecto.edificio)
            dist   = geom.dist_max_evacuacion_m
            cumple = dist <= max_evac
            resultados.append(ResultadoValidacion(
                regla="evacuacion.dist_max",
                cumple=cumple,
                mensaje=(
                    f"[{planta.nombre}] Dist. evacuación {dist:.1f} m "
                    f"{'≤' if cumple else '>'} máximo {max_evac:.0f} m"
                ),
                valor_real=dist,
                valor_limite=max_evac,
            ))
        return resultados
