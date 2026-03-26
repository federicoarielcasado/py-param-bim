"""
prueba_generador_planta.py
--------------------------
Tests del generador de layout de planta tipo (Sprint 6).

Valida:
    - Dimensiones de la huella (retiros aplicados correctamente)
    - Posición del core (izquierda, centrado verticalmente)
    - Posición del pasillo (centrado vertical, ancho correcto)
    - Distribución de unidades dentro de la huella
    - Cálculo de distancia máxima de evacuación
    - Distribución de ambientes dentro de cada unidad
    - GeneradorArquitectonico.generar()
    - GeneradorCirculacion.metricas_planta()
"""
import pytest
import math

from bim_generador.nucleo.motor_parametros import (
    Proyecto, TipoUnidad, Unidad,
)
from bim_generador.generadores.planta import (
    GeneradorPlanta, _distribuir_ambientes,
    GeometriaPlanta, GeometriaUnidad, RectAmbiente,
)
from bim_generador.generadores.circulacion   import GeneradorCirculacion
from bim_generador.generadores.arquitectonico import GeneradorArquitectonico


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def proyecto_default():
    return Proyecto.desde_predeterminados("Test")


@pytest.fixture
def gen():
    return GeneradorPlanta()


@pytest.fixture
def geom_default(proyecto_default, gen):
    p = proyecto_default
    planta = next(pl for pl in p.edificio.plantas if pl.numero > 0)
    return gen.generar(planta, p.lote, p.edificio)


# ---------------------------------------------------------------------------
# Dimensiones de la huella
# ---------------------------------------------------------------------------

class PruebaDimensionesPlanta:

    def prueba_ancho_aplica_retiros_laterales(self, proyecto_default, gen):
        p = proyecto_default
        planta = p.edificio.plantas[0]
        geom = gen.generar(planta, p.lote, p.edificio)
        esperado = p.lote.frente_m - 2 * p.edificio.retiro_lateral_m
        assert abs(geom.ancho_total - esperado) < 0.01

    def prueba_fondo_aplica_retiros(self, proyecto_default, gen):
        p = proyecto_default
        planta = p.edificio.plantas[0]
        geom = gen.generar(planta, p.lote, p.edificio)
        esperado = (
            p.lote.fondo_m
            - p.edificio.retiro_frontal_m
            - p.edificio.retiro_posterior_m
        )
        assert abs(geom.fondo_total - esperado) < 0.01

    def prueba_minimo_ancho_5m(self, proyecto_default, gen):
        p = proyecto_default
        p.lote.frente_m = 2.0
        planta = p.edificio.plantas[0]
        geom = gen.generar(planta, p.lote, p.edificio)
        assert geom.ancho_total >= 5.0

    def prueba_minimo_fondo_8m(self, proyecto_default, gen):
        p = proyecto_default
        p.lote.fondo_m = 1.0
        planta = p.edificio.plantas[0]
        geom = gen.generar(planta, p.lote, p.edificio)
        assert geom.fondo_total >= 8.0


# ---------------------------------------------------------------------------
# Core (núcleo vertical)
# ---------------------------------------------------------------------------

class PruebaCore:

    def prueba_core_x_en_origen(self, geom_default):
        assert geom_default.core.x == 0.0

    def prueba_core_ancho_igual_nucleo(self, proyecto_default, geom_default):
        nucleo = proyecto_default.edificio.plantas[1].nucleo
        assert abs(geom_default.core.ancho - nucleo.ancho_m) < 1e-9

    def prueba_core_centrado_verticalmente(self, geom_default):
        core = geom_default.core
        D = geom_default.fondo_total
        centro_core = core.y + core.alto / 2
        assert abs(centro_core - D / 2) < 0.01

    def prueba_core_dentro_de_la_planta(self, geom_default):
        core = geom_default.core
        assert core.x >= 0
        assert core.y >= 0
        assert core.y + core.alto <= geom_default.fondo_total + 0.01


# ---------------------------------------------------------------------------
# Pasillo de distribución
# ---------------------------------------------------------------------------

class PruebaPasillo:

    def prueba_pasillo_comienza_en_core(self, geom_default):
        assert abs(geom_default.pasillo.x - geom_default.core.ancho) < 1e-9

    def prueba_pasillo_centrado_verticalmente(self, geom_default):
        pasillo = geom_default.pasillo
        D = geom_default.fondo_total
        centro_pasillo = pasillo.y + pasillo.alto / 2
        assert abs(centro_pasillo - D / 2) < 0.01

    def prueba_pasillo_ancho_correcto(self, proyecto_default, geom_default):
        planta = next(pl for pl in proyecto_default.edificio.plantas if pl.numero > 0)
        assert abs(geom_default.pasillo.alto - planta.ancho_pasillo_m) < 1e-9

    def prueba_pasillo_llega_hasta_borde_derecho(self, geom_default):
        pasillo = geom_default.pasillo
        assert abs(pasillo.x + pasillo.ancho - geom_default.ancho_total) < 0.01


# ---------------------------------------------------------------------------
# Distribución de unidades
# ---------------------------------------------------------------------------

class PruebaDistribucionUnidades:

    def prueba_cantidad_unidades_correcta(self, proyecto_default, geom_default):
        planta = next(pl for pl in proyecto_default.edificio.plantas if pl.numero > 0)
        assert len(geom_default.unidades) == len(planta.unidades)

    def prueba_unidades_dentro_de_la_huella(self, geom_default):
        W, D = geom_default.ancho_total, geom_default.fondo_total
        for u in geom_default.unidades:
            assert u.x >= geom_default.core.ancho - 0.01
            assert u.y >= -0.01
            assert u.x + u.ancho <= W + 0.01
            assert u.y + u.alto  <= D + 0.01

    def prueba_unidades_no_solapan_pasillo(self, geom_default):
        pasillo = geom_default.pasillo
        p_y0, p_y1 = pasillo.y, pasillo.y + pasillo.alto
        for u in geom_default.unidades:
            solapamiento = (u.y < p_y1) and (u.y + u.alto > p_y0)
            assert not solapamiento, f"Unidad {u.unidad.codigo} solapa con el pasillo"

    def prueba_lados_asignados_correctamente(self, geom_default):
        pasillo = geom_default.pasillo
        for u in geom_default.unidades:
            if u.lado == "sur":
                assert u.y + u.alto <= pasillo.y + 0.01
            else:
                assert u.y >= pasillo.y + pasillo.alto - 0.01


# ---------------------------------------------------------------------------
# Distancia de evacuación
# ---------------------------------------------------------------------------

class PruebaEvacuacion:

    def prueba_dist_positiva(self, geom_default):
        assert geom_default.dist_max_evacuacion_m > 0

    def prueba_dist_menor_que_diagonal(self, geom_default):
        diagonal = math.sqrt(
            geom_default.ancho_total ** 2 + geom_default.fondo_total ** 2
        )
        assert geom_default.dist_max_evacuacion_m <= diagonal + 0.01

    def prueba_planta_sin_unidades_da_cero(self, proyecto_default, gen):
        from bim_generador.nucleo.motor_parametros import Planta, TipoPlanta
        planta_vacia = Planta(numero=99, tipo_planta=TipoPlanta.PLANTA_TIPO)
        geom = gen.generar(planta_vacia, proyecto_default.lote, proyecto_default.edificio)
        assert geom.dist_max_evacuacion_m == 0.0


# ---------------------------------------------------------------------------
# Ambientes dentro de las unidades
# ---------------------------------------------------------------------------

class PruebaAmbientesEnUnidades:

    def prueba_ambientes_tienen_area_positiva(self, geom_default):
        for u in geom_default.unidades:
            for ra in u.ambientes_geom:
                assert ra.ancho > 0
                assert ra.alto  > 0

    def prueba_ambientes_dentro_del_bounding_box(self, geom_default):
        for u in geom_default.unidades:
            for ra in u.ambientes_geom:
                assert ra.x >= u.x - 0.01
                assert ra.y >= u.y - 0.01
                assert ra.x + ra.ancho <= u.x + u.ancho + 0.01
                assert ra.y + ra.alto  <= u.y + u.alto  + 0.01

    def prueba_distribuir_sin_ambientes(self):
        assert _distribuir_ambientes([], 0, 0, 10, 10) == []

    def prueba_distribuir_bbox_cero(self):
        from bim_generador.nucleo.motor_parametros import TipoAmbiente, Ambiente
        ams = [Ambiente.predeterminados_por_tipo(TipoAmbiente.LIVING_COMEDOR)]
        assert _distribuir_ambientes(ams, 0, 0, 0, 10) == []
        assert _distribuir_ambientes(ams, 0, 0, 10, 0) == []


# ---------------------------------------------------------------------------
# GeneradorArquitectonico
# ---------------------------------------------------------------------------

class PruebaGeneradorArquitectonico:

    def prueba_generar_retorna_una_por_planta(self, proyecto_default):
        gen_arq = GeneradorArquitectonico()
        resultado = gen_arq.generar(proyecto_default)
        assert len(resultado) == len(proyecto_default.edificio.plantas)

    def prueba_generar_planta_por_indice(self, proyecto_default):
        gen_arq = GeneradorArquitectonico()
        geom = gen_arq.generar_planta(proyecto_default, planta_idx=0)
        assert isinstance(geom, GeometriaPlanta)

    def prueba_indice_fuera_de_rango_usa_ultima(self, proyecto_default):
        gen_arq = GeneradorArquitectonico()
        n = len(proyecto_default.edificio.plantas)
        geom = gen_arq.generar_planta(proyecto_default, planta_idx=999)
        assert geom.planta.numero == proyecto_default.edificio.plantas[n - 1].numero

    def prueba_edificio_sin_plantas_lanza_error(self):
        p = Proyecto.desde_predeterminados("Vacío")
        p.edificio.plantas = []
        gen_arq = GeneradorArquitectonico()
        with pytest.raises(ValueError):
            gen_arq.generar_planta(p)


# ---------------------------------------------------------------------------
# GeneradorCirculacion
# ---------------------------------------------------------------------------

class PruebaGeneradorCirculacion:

    def prueba_metricas_contiene_claves_requeridas(self, geom_default):
        gen_circ = GeneradorCirculacion()
        m = gen_circ.metricas_planta(geom_default)
        claves = {
            "dist_max_evacuacion_m", "ancho_pasillo_m",
            "sup_pasillo_m2", "sup_core_m2",
            "ratio_circulacion", "cantidad_unidades",
        }
        assert claves.issubset(m.keys())

    def prueba_ratio_circulacion_entre_0_y_1(self, geom_default):
        gen_circ = GeneradorCirculacion()
        m = gen_circ.metricas_planta(geom_default)
        assert 0.0 <= m["ratio_circulacion"] <= 1.0

    def prueba_generar_nucleos_uno_por_planta(self, proyecto_default):
        gen_circ = GeneradorCirculacion()
        nucleos = gen_circ.generar_nucleos(proyecto_default.edificio)
        assert len(nucleos) == len(proyecto_default.edificio.plantas)
        for n in nucleos:
            assert n["ancho"] > 0
            assert n["largo"] > 0
