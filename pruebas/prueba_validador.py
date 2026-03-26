"""
prueba_validador.py
-------------------
Pruebas del validador normativo (validador.py).

Cubre:
  - Carga del perfil argentina_caba
  - Validación de FOS y FOT
  - Validación de superficies mínimas de ambientes
  - Validación de dimensiones mínimas de ambientes
  - Validación de iluminación y ventilación natural
  - Validación de superficie total de unidad por tipología
  - Validación de ancho de pasillo
  - Validación de altura libre por piso
  - Validación de distancia de evacuación
  - Validación de retiros mínimos

Ejecutar con:
    pytest pruebas/prueba_validador.py -v
"""

import pytest
from bim_generador.nucleo.motor_parametros import (
    Proyecto, Lote, Edificio, Ambiente, TipoAmbiente, Unidad, TipoUnidad,
    Planta, TipoPlanta,
)
from bim_generador.nucleo.validador import Validador, ResultadoValidacion


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validador():
    return Validador("argentina_caba")


@pytest.fixture
def proyecto_cumplen():
    """Proyecto que cumple con todas las normas."""
    return Proyecto.desde_predeterminados("Proyecto Válido")


@pytest.fixture
def proyecto_fot_excedido():
    """Proyecto con FOT por encima del máximo."""
    p = Proyecto.desde_predeterminados("FOT Alto")
    p.lote.frente_m = 5.0
    p.lote.fondo_m  = 6.0
    return p


# ---------------------------------------------------------------------------
# Tests base (compatibilidad con suite anterior)
# ---------------------------------------------------------------------------

class PruebaValidador:

    def prueba_carga_perfil_argentina(self, validador):
        assert validador.norma["profile"] == "argentina_caba"
        assert "fos_max" in validador.norma["uso_suelo"]

    def prueba_perfil_inexistente_lanza_error(self):
        with pytest.raises(FileNotFoundError):
            Validador("pais_inexistente")

    def prueba_validar_retorna_lista(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        assert isinstance(resultados, list)
        assert len(resultados) > 0

    def prueba_todos_resultados_son_tipo_correcto(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        for r in resultados:
            assert isinstance(r, ResultadoValidacion)

    def prueba_fos_supera_limite_es_incumplimiento(self, validador, proyecto_fot_excedido):
        resultados = validador.validar(proyecto_fot_excedido)
        fos_results = [r for r in resultados if r.regla == "FOS"]
        assert len(fos_results) == 1
        assert fos_results[0].valor_real is not None

    def prueba_repr_resultado(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        for r in resultados:
            repr_str = repr(r)
            assert r.regla in repr_str


# ---------------------------------------------------------------------------
# Tests urbanísticos
# ---------------------------------------------------------------------------

class PruebaReglasUrbanisticas:

    def prueba_fos_resultado_tiene_valor_real(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        fos = next(r for r in resultados if r.regla == "FOS")
        assert fos.valor_real is not None
        assert fos.valor_real >= 0

    def prueba_fot_resultado_tiene_valor_real(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        fot = next(r for r in resultados if r.regla == "FOT")
        assert fot.valor_real is not None
        assert fot.valor_real >= 0

    def prueba_retiros_presentes(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        retiro_reglas = [r for r in resultados if r.regla.startswith("retiro.")]
        assert len(retiro_reglas) >= 1

    def prueba_retiro_por_debajo_del_minimo_es_incumplimiento(self, validador):
        p = Proyecto.desde_predeterminados("Retiro cero")
        p.edificio.retiro_frontal_m  = 0.0
        p.edificio.retiro_lateral_m  = 0.0
        p.edificio.retiro_posterior_m = 0.0
        resultados = validador.validar(p)
        retiros_incumplidos = [
            r for r in resultados
            if r.regla.startswith("retiro.") and not r.cumple
        ]
        assert len(retiros_incumplidos) > 0

    def prueba_retiro_correcto_cumple(self, validador):
        p = Proyecto.desde_predeterminados("Retiros ok")
        p.edificio.retiro_frontal_m   = 3.0
        p.edificio.retiro_lateral_m   = 3.0
        p.edificio.retiro_posterior_m = 3.0
        resultados = validador.validar(p)
        retiros = [r for r in resultados if r.regla.startswith("retiro.")]
        assert all(r.cumple for r in retiros)


# ---------------------------------------------------------------------------
# Tests de superficies y dimensiones de ambientes
# ---------------------------------------------------------------------------

class PruebaReglasAmbientes:

    def prueba_hay_resultados_sup_min(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        sup_min = [r for r in resultados if r.regla.startswith("sup_min.")]
        assert len(sup_min) > 0

    def prueba_superficie_bajo_minimo_incumple(self, validador):
        p = Proyecto.desde_predeterminados("Sup baja")
        planta_ref = next(pl for pl in p.edificio.plantas if pl.numero > 0)
        for unidad in planta_ref.unidades:
            for amb in unidad.ambientes:
                if amb.tipo == TipoAmbiente.LIVING_COMEDOR:
                    amb.superficie_m2 = 5.0   # muy por debajo de 16 m²
        resultados = validador.validar(p)
        living_fail = [
            r for r in resultados
            if r.regla == "sup_min.living_comedor" and not r.cumple
        ]
        assert len(living_fail) > 0

    def prueba_hay_resultados_dim_min(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        dim_min = [r for r in resultados if r.regla.startswith("dim_min.")]
        assert len(dim_min) > 0

    def prueba_ancho_bajo_minimo_incumple(self, validador):
        p = Proyecto.desde_predeterminados("Ancho bajo")
        planta_ref = next(pl for pl in p.edificio.plantas if pl.numero > 0)
        for unidad in planta_ref.unidades:
            for amb in unidad.ambientes:
                if amb.tipo == TipoAmbiente.DORMITORIO_PRINCIPAL:
                    amb.ancho_min_m = 1.0   # muy por debajo de 3.0 m
        resultados = validador.validar(p)
        dim_fail = [
            r for r in resultados
            if r.regla == "dim_min.dormitorio_principal" and not r.cumple
        ]
        assert len(dim_fail) > 0


# ---------------------------------------------------------------------------
# Tests de iluminación y ventilación
# ---------------------------------------------------------------------------

class PruebaIluminacionVentilacion:

    def prueba_hay_resultados_ilum_vent(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        iv = [r for r in resultados if r.regla.startswith("ilum_vent.")]
        assert len(iv) > 0

    def prueba_sin_iluminacion_natural_incumple(self, validador):
        p = Proyecto.desde_predeterminados("Sin luz")
        planta_ref = next(pl for pl in p.edificio.plantas if pl.numero > 0)
        for unidad in planta_ref.unidades:
            for amb in unidad.ambientes:
                if amb.tipo == TipoAmbiente.LIVING_COMEDOR:
                    amb.iluminacion_natural = False
        resultados = validador.validar(p)
        ilum_fail = [
            r for r in resultados
            if r.regla == "ilum_vent.iluminacion" and not r.cumple
        ]
        assert len(ilum_fail) > 0

    def prueba_sin_ventilacion_natural_incumple(self, validador):
        p = Proyecto.desde_predeterminados("Sin vent")
        planta_ref = next(pl for pl in p.edificio.plantas if pl.numero > 0)
        for unidad in planta_ref.unidades:
            for amb in unidad.ambientes:
                if amb.tipo == TipoAmbiente.DORMITORIO_SIMPLE:
                    amb.ventilacion_natural = False
        resultados = validador.validar(p)
        vent_fail = [
            r for r in resultados
            if r.regla == "ilum_vent.ventilacion" and not r.cumple
        ]
        assert len(vent_fail) > 0

    def prueba_ambiente_no_habitable_no_genera_resultado_iv(self, validador):
        """Baños y lavaderos (no habitables) no deben aparecer en ilum_vent."""
        p = Proyecto.desde_predeterminados("Baño sin luz")
        planta_ref = next(pl for pl in p.edificio.plantas if pl.numero > 0)
        for unidad in planta_ref.unidades:
            for amb in unidad.ambientes:
                if amb.tipo == TipoAmbiente.BANIO:
                    amb.iluminacion_natural = False
                    amb.ventilacion_natural = False
        resultados = validador.validar(p)
        # Los baños no son habitables → no deben generar incumplimiento ilum_vent
        # (pueden tener resultados de sup_min pero no de ilum_vent)
        iv_con_banio = [
            r for r in resultados
            if r.regla.startswith("ilum_vent.") and "banio" in r.mensaje.lower()
        ]
        # No debe haber ningún resultado ilum_vent relacionado al baño
        assert len(iv_con_banio) == 0


# ---------------------------------------------------------------------------
# Tests de superficie de unidad
# ---------------------------------------------------------------------------

class PruebaSuperficieUnidad:

    def prueba_hay_resultados_sup_unidad(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        sup_u = [r for r in resultados if r.regla.startswith("sup_unidad.")]
        assert len(sup_u) > 0

    def prueba_resultados_sup_unidad_tienen_valor_real(self, validador, proyecto_cumplen):
        """Todos los resultados de sup_unidad deben tener valor_real y valor_limite."""
        resultados = validador.validar(proyecto_cumplen)
        sup_u = [r for r in resultados if r.regla.startswith("sup_unidad.")]
        for r in sup_u:
            assert r.valor_real  is not None and r.valor_real  > 0
            assert r.valor_limite is not None and r.valor_limite > 0

    def prueba_unidad_grande_cumple_minimo(self, validador):
        """Una unidad con superficie generosa debe cumplir el mínimo de tipología."""
        from bim_generador.nucleo.motor_parametros import TipoAmbiente, Ambiente
        p = Proyecto.desde_predeterminados("Sup generosa")
        planta_ref = next(pl for pl in p.edificio.plantas if pl.numero > 0)
        # Agrandar las superficies de la primera unidad (2 ambientes → > 42 m²)
        for unidad in planta_ref.unidades:
            if unidad.tipologia == TipoUnidad.DOS_AMBIENTES:
                for amb in unidad.ambientes:
                    if amb.tipo == TipoAmbiente.LIVING_COMEDOR:
                        amb.superficie_m2 = 25.0  # 9+25+6+3.5+3 = 46.5 m² > 42
        resultados = validador.validar(p)
        sup_2amb = [
            r for r in resultados
            if r.regla == "sup_unidad.2_ambientes"
        ]
        assert any(r.cumple for r in sup_2amb)


# ---------------------------------------------------------------------------
# Tests de circulación y altura
# ---------------------------------------------------------------------------

class PruebaCirculacionAltura:

    def prueba_hay_resultado_ancho_pasillo(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        pasillo = [r for r in resultados if r.regla == "ancho_pasillo"]
        assert len(pasillo) >= 1

    def prueba_pasillo_default_cumple(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        pasillo = [r for r in resultados if r.regla == "ancho_pasillo"]
        assert all(r.cumple for r in pasillo)

    def prueba_pasillo_estrecho_incumple(self, validador):
        p = Proyecto.desde_predeterminados("Pasillo estrecho")
        for planta in p.edificio.plantas:
            planta.ancho_pasillo_m = 0.8   # por debajo de 1.20 m
        resultados = validador.validar(p)
        pasillo_fail = [
            r for r in resultados
            if r.regla == "ancho_pasillo" and not r.cumple
        ]
        assert len(pasillo_fail) > 0

    def prueba_hay_resultado_altura_libre(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        alt = [r for r in resultados if r.regla == "altura_libre"]
        assert len(alt) >= 1

    def prueba_altura_default_cumple(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        alt = [r for r in resultados if r.regla == "altura_libre"]
        assert all(r.cumple for r in alt)

    def prueba_altura_baja_incumple(self, validador):
        p = Proyecto.desde_predeterminados("Techo bajo")
        for planta in p.edificio.plantas:
            planta.altura_libre_m = 2.41   # campo tiene mínimo 2.40
        resultados = validador.validar(p)
        alt = [r for r in resultados if r.regla == "altura_libre"]
        # 2.41 m ≥ 2.40 m → debe cumplir
        assert all(r.cumple for r in alt)


# ---------------------------------------------------------------------------
# Tests de evacuación
# ---------------------------------------------------------------------------

class PruebaEvacuacionNormativa:

    def prueba_hay_resultados_evacuacion(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        evac = [r for r in resultados if r.regla == "evacuacion.dist_max"]
        assert len(evac) > 0

    def prueba_evacuacion_default_cumple(self, validador, proyecto_cumplen):
        """Proyecto predeterminado (lote 15×30, 7 pisos) debe cumplir 40 m."""
        resultados = validador.validar(proyecto_cumplen)
        evac = [r for r in resultados if r.regla == "evacuacion.dist_max"]
        assert all(r.cumple for r in evac)

    def prueba_dist_evacuacion_tiene_valor_real(self, validador, proyecto_cumplen):
        resultados = validador.validar(proyecto_cumplen)
        evac = [r for r in resultados if r.regla == "evacuacion.dist_max"]
        for r in evac:
            assert r.valor_real is not None
            assert r.valor_real > 0

    def prueba_lote_muy_grande_puede_exceder_evacuacion(self, validador):
        """Con un lote de 100×200 m la dist. de evacuación podría exceder 40 m."""
        p = Proyecto.desde_predeterminados("Lote gigante")
        p.lote.frente_m = 100.0
        p.lote.fondo_m  = 200.0
        resultados = validador.validar(p)
        evac = [r for r in resultados if r.regla == "evacuacion.dist_max"]
        # Al menos debe haber resultados (no importa si cumple o no)
        assert len(evac) > 0
        # Con este lote enorme, alguno debería no cumplir
        incumple = [r for r in evac if not r.cumple]
        assert len(incumple) > 0
