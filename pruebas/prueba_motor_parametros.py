"""
prueba_motor_parametros.py
--------------------------
Pruebas del motor de parámetros (motor_parametros.py).

Cubre:
  - Creación de modelos individuales (Ambiente, Unidad, Planta, Lote, Edificio, Proyecto)
  - Campos computados (superficie_total, altura_total, etc.)
  - Defaults por tipología
  - Serialización y deserialización JSON
  - Generación de plantas desde parámetros

Ejecutar con:
    pytest pruebas/prueba_motor_parametros.py -v
"""

import json
import pytest
from bim_generador.nucleo.motor_parametros import (
    Ambiente, TipoAmbiente,
    Unidad, TipoUnidad,
    Planta, TipoPlanta, NucleoVertical,
    Lote,
    Edificio, ParametrosEstructurales,
    Proyecto, MetadatosProyecto,
)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def ambiente_dormitorio():
    return Ambiente.predeterminados_por_tipo(TipoAmbiente.DORMITORIO_SIMPLE)


@pytest.fixture
def unidad_2amb():
    return Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES, codigo="A")


@pytest.fixture
def proyecto_predeterminado():
    return Proyecto.desde_predeterminados("Test Edificio")


# ===========================================================================
# Pruebas de Ambiente
# ===========================================================================

class PruebaAmbiente:

    def prueba_crear_ambiente_basico(self):
        amb = Ambiente(tipo=TipoAmbiente.COCINA, superficie_m2=7.0, ancho_min_m=2.2)
        assert amb.superficie_m2 == 7.0
        assert amb.tipo == TipoAmbiente.COCINA

    def prueba_predeterminados_por_tipo(self):
        dormitorio = Ambiente.predeterminados_por_tipo(TipoAmbiente.DORMITORIO_PRINCIPAL)
        assert dormitorio.superficie_m2 == 12.0
        assert dormitorio.ancho_min_m == 3.0
        assert dormitorio.iluminacion_natural is True

    def prueba_nombre_por_defecto(self, ambiente_dormitorio):
        assert "dormitorio" in ambiente_dormitorio.nombre.lower()

    def prueba_nombre_custom(self):
        amb = Ambiente(tipo=TipoAmbiente.DORMITORIO_SIMPLE,
                       superficie_m2=10.0, ancho_min_m=2.5,
                       nombre_custom="Suite Principal")
        assert amb.nombre == "Suite Principal"

    def prueba_superficie_positiva(self):
        with pytest.raises(Exception):
            Ambiente(tipo=TipoAmbiente.COCINA, superficie_m2=-5.0, ancho_min_m=2.0)

    def prueba_todos_los_tipos_tienen_predeterminados(self):
        for tipo in TipoAmbiente:
            amb = Ambiente.predeterminados_por_tipo(tipo)
            assert amb.superficie_m2 > 0


# ===========================================================================
# Pruebas de Unidad
# ===========================================================================

class PruebaUnidad:

    def prueba_superficie_total_computada(self, unidad_2amb):
        esperado = sum(a.superficie_m2 for a in unidad_2amb.ambientes)
        assert unidad_2amb.superficie_total_m2 == round(esperado, 2)

    def prueba_superficie_vendible_excluye_circulacion(self, unidad_2amb):
        total    = unidad_2amb.superficie_total_m2
        vendible = unidad_2amb.superficie_vendible_m2
        assert vendible <= total

    def prueba_cantidad_dormitorios(self, unidad_2amb):
        assert unidad_2amb.cantidad_dormitorios == 1  # 2 ambientes = 1 dormitorio

    def prueba_tres_ambientes_tiene_dos_dormitorios(self):
        u = Unidad.desde_tipologia(TipoUnidad.TRES_AMBIENTES)
        assert u.cantidad_dormitorios == 2

    def prueba_tipologias_generan_ambientes(self):
        for tipo in (TipoUnidad.MONOAMBIENTE, TipoUnidad.DOS_AMBIENTES,
                     TipoUnidad.TRES_AMBIENTES, TipoUnidad.CUATRO_AMBIENTES):
            u = Unidad.desde_tipologia(tipo)
            assert len(u.ambientes) > 0

    def prueba_monoambiente_sin_dormitorio_separado(self):
        u = Unidad.desde_tipologia(TipoUnidad.MONOAMBIENTE)
        assert u.cantidad_dormitorios == 0


# ===========================================================================
# Pruebas de Planta
# ===========================================================================

class PruebaPlanta:

    def prueba_cantidad_unidades(self, unidad_2amb):
        planta = Planta(numero=1, unidades=[unidad_2amb, unidad_2amb])
        assert planta.cantidad_unidades == 2

    def prueba_nombre_planta_baja(self):
        pb = Planta(numero=0, tipo_planta=TipoPlanta.PLANTA_BAJA)
        assert pb.nombre == "Planta Baja"

    def prueba_nombre_ultimo_piso(self):
        up = Planta(numero=8, tipo_planta=TipoPlanta.ULTIMO_PISO)
        assert "Último" in up.nombre

    def prueba_nucleo_vertical_por_defecto(self):
        planta = Planta(numero=1)
        assert planta.nucleo.tiene_ascensor is True
        assert planta.nucleo.superficie_m2 > 0

    def prueba_altura_libre_minima(self):
        with pytest.raises(Exception):
            Planta(numero=1, altura_libre_m=2.0)  # mínimo 2.4


# ===========================================================================
# Pruebas de Lote
# ===========================================================================

class PruebaLote:

    def prueba_superficie_computada(self):
        lote = Lote(frente_m=15.0, fondo_m=30.0)
        assert lote.superficie_m2 == 450.0

    def prueba_superficie_edificable(self):
        lote = Lote(frente_m=20.0, fondo_m=25.0, fos_max=0.6)
        assert lote.superficie_edificable_m2 == 300.0  # 500 * 0.6

    def prueba_superficie_total_construible(self):
        lote = Lote(frente_m=20.0, fondo_m=25.0, fot_max=2.5)
        assert lote.superficie_total_construible_m2 == 1250.0  # 500 * 2.5

    def prueba_fos_max_entre_0_y_1(self):
        with pytest.raises(Exception):
            Lote(frente_m=15.0, fondo_m=30.0, fos_max=1.5)


# ===========================================================================
# Pruebas de Edificio
# ===========================================================================

class PruebaEdificio:

    def prueba_generar_plantas_tipo(self):
        ed = Edificio(nombre="Test", cantidad_pisos=5)
        unidades = [Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES)]
        ed.generar_plantas_tipo(unidades)

        total_esperado = 5 + 1  # 5 pisos + PB
        assert len(ed.plantas) == total_esperado

    def prueba_primera_planta_es_pb(self):
        ed = Edificio(nombre="Test", cantidad_pisos=3, incluye_pb=True)
        ed.generar_plantas_tipo([Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES)])
        assert ed.plantas[0].tipo_planta == TipoPlanta.PLANTA_BAJA

    def prueba_ultima_planta_es_ultimo_piso(self):
        ed = Edificio(nombre="Test", cantidad_pisos=4)
        ed.generar_plantas_tipo([Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES)])
        assert ed.plantas[-1].tipo_planta == TipoPlanta.ULTIMO_PISO

    def prueba_altura_total_positiva(self):
        ed = Edificio(nombre="Test", cantidad_pisos=7)
        ed.generar_plantas_tipo([Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES)])
        assert ed.altura_total_m > 0

    def prueba_total_unidades(self):
        ed = Edificio(nombre="Test", cantidad_pisos=3)
        # 2 unidades por planta, 4 plantas (PB + 3 pisos)
        unidades = [
            Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES, codigo="A"),
            Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES, codigo="B"),
        ]
        ed.generar_plantas_tipo(unidades)
        assert ed.total_unidades == 4 * 2  # 4 plantas × 2 unidades


# ===========================================================================
# Pruebas de Proyecto
# ===========================================================================

class PruebaProyecto:

    def prueba_desde_predeterminados_crea_proyecto_valido(self, proyecto_predeterminado):
        assert proyecto_predeterminado.nombre == "Test Edificio"
        assert proyecto_predeterminado.lote.superficie_m2 > 0
        assert len(proyecto_predeterminado.edificio.plantas) > 0

    def prueba_fos_real_entre_0_y_1(self, proyecto_predeterminado):
        fos = proyecto_predeterminado.calcular_fos_real()
        assert 0.0 <= fos <= 1.0

    def prueba_fot_real_positivo(self, proyecto_predeterminado):
        fot = proyecto_predeterminado.calcular_fot_real()
        assert fot >= 0.0

    def prueba_resumen_tiene_claves_esperadas(self, proyecto_predeterminado):
        resumen = proyecto_predeterminado.resumen()
        claves_esperadas = [
            "nombre", "lote_m2", "cantidad_pisos",
            "altura_total_m", "total_unidades", "fos_real", "fot_real",
        ]
        for clave in claves_esperadas:
            assert clave in resumen, f"Falta clave: {clave}"

    def prueba_serializacion_json_roundtrip(self, proyecto_predeterminado):
        json_str = proyecto_predeterminado.a_json()
        assert json_str  # no vacío

        proyecto_cargado = Proyecto.desde_json(json_str)
        assert proyecto_cargado.nombre == proyecto_predeterminado.nombre
        assert proyecto_cargado.lote.frente_m == proyecto_predeterminado.lote.frente_m
        assert len(proyecto_cargado.edificio.plantas) == len(proyecto_predeterminado.edificio.plantas)

    def prueba_json_es_valido(self, proyecto_predeterminado):
        json_str = proyecto_predeterminado.a_json()
        data = json.loads(json_str)
        assert "nombre" in data
        assert "lote" in data
        assert "edificio" in data

    def prueba_nombre_edificio_sincronizado(self):
        p = Proyecto(nombre="Torres del Parque")
        assert p.edificio.nombre == "Torres del Parque"

    def prueba_modificar_lote_actualiza_metricas(self, proyecto_predeterminado):
        fot_antes = proyecto_predeterminado.calcular_fot_real()
        proyecto_predeterminado.lote.frente_m = 30.0  # lote más grande → FOT baja
        fot_despues = proyecto_predeterminado.calcular_fot_real()
        assert fot_despues < fot_antes
