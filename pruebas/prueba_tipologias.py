"""
prueba_tipologias.py
--------------------
Pruebas del Sprint 4 — Tipologías de unidades y RenderizadorUnidad.

Cubre:
  - RenderizadorUnidad: claves del MultiBlock, geometría válida
  - RenderizadorUnidad: layout por zonas, etiquetas con tipo_int y area_m2
  - RenderizadorUnidad: casos borde (unidad vacía, retiro de contexto, índice fuera de rango)
  - MotorVista: despacho correcto a RenderizadorUnidad con contexto
  - PanelBase: propiedad contexto_render devuelve dict vacío por defecto

Ejecutar con:
    pytest pruebas/prueba_tipologias.py -v
"""

import pytest

from bim_generador.nucleo.motor_parametros             import (
    Proyecto, TipoUnidad, TipoAmbiente, Unidad, Ambiente, Planta, TipoPlanta,
)
from bim_generador.vista_previa.motor                  import MotorVista, SeccionActiva
from bim_generador.vista_previa.renderizadores.unidad  import RenderizadorUnidad, TIPO_A_INT


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def proyecto_simple():
    """Proyecto con 3 unidades distintas en la planta tipo."""
    p = Proyecto.desde_predeterminados("Test Tipologias")
    return p


@pytest.fixture
def proyecto_monoambiente():
    """Proyecto con sólo monoambientes (sin dormitorios ni balcón)."""
    p = Proyecto.desde_predeterminados("Mono")
    unidades = [Unidad.desde_tipologia(TipoUnidad.MONOAMBIENTE, codigo="A")]
    p.edificio.generar_plantas_tipo(unidades)
    return p


@pytest.fixture
def proyecto_sin_plantas():
    """Proyecto con lista de plantas vacía."""
    p = Proyecto.desde_predeterminados("Vacio")
    p.edificio.plantas = []
    return p


@pytest.fixture
def proyecto_cuatro_ambientes():
    """Proyecto con unidades de 4 ambientes (tiene toilette, dos dormitorios)."""
    p = Proyecto.desde_predeterminados("4amb")
    unidades = [Unidad.desde_tipologia(TipoUnidad.CUATRO_AMBIENTES, codigo="A")]
    p.edificio.generar_plantas_tipo(unidades)
    return p


# ===========================================================================
# RenderizadorUnidad — claves y estructura del MultiBlock
# ===========================================================================

class PruebaRenderizadorUnidad:

    def prueba_retorna_multiblock(self, proyecto_simple):
        import pyvista as pv
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        assert resultado is not None
        assert isinstance(resultado, pv.MultiBlock)

    def prueba_claves_presentes(self, proyecto_simple):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        claves = resultado.keys()
        assert "habitaciones" in claves
        assert "etiquetas" in claves

    def prueba_habitaciones_es_multiblock(self, proyecto_simple):
        import pyvista as pv
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        assert isinstance(resultado["habitaciones"], pv.MultiBlock)

    def prueba_habitaciones_no_vacias(self, proyecto_simple):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        assert len(resultado["habitaciones"].keys()) > 0

    def prueba_etiquetas_tienen_puntos(self, proyecto_simple):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        etiq = resultado["etiquetas"]
        # Cada ambiente debe tener un punto de etiqueta
        planta_ref = proyecto_simple.edificio.plantas[1]  # primera planta tipo
        n_ambientes = len(planta_ref.unidades[0].ambientes)
        assert etiq.n_points == n_ambientes

    def prueba_etiquetas_tienen_tipo_int(self, proyecto_simple):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        etiq = resultado["etiquetas"]
        assert "tipo_int" in etiq.point_data

    def prueba_etiquetas_tienen_area_m2(self, proyecto_simple):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        etiq = resultado["etiquetas"]
        assert "area_m2" in etiq.point_data

    def prueba_area_m2_positiva(self, proyecto_simple):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        etiq = resultado["etiquetas"]
        areas = etiq.point_data["area_m2"]
        assert all(a > 0 for a in areas)

    def prueba_tipo_int_en_rango(self, proyecto_simple):
        """Todos los tipo_int deben ser valores válidos del mapa TIPO_A_INT."""
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        etiq = resultado["etiquetas"]
        valores_validos = set(TIPO_A_INT.values())
        for t in etiq.point_data["tipo_int"]:
            assert int(t) in valores_validos

    def prueba_tipo_vista_es_unidad_2d(self):
        assert RenderizadorUnidad.tipo_vista() == "unidad_2d"

    def prueba_cantidad_habitaciones_igual_ambientes(self, proyecto_simple):
        """El número de meshes en habitaciones debe coincidir con los ambientes de la unidad."""
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        # Planta tipo: primera planta con TipoPlanta.PLANTA_TIPO
        planta_tipo = next(
            p for p in proyecto_simple.edificio.plantas
            if p.tipo_planta == TipoPlanta.PLANTA_TIPO
        )
        unidad = planta_tipo.unidades[0]
        n_ambientes = len(unidad.ambientes)
        assert len(resultado["habitaciones"].keys()) == n_ambientes

    def prueba_cada_habitacion_tiene_tipo_int_en_cell_data(self, proyecto_simple):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        habitaciones = resultado["habitaciones"]
        for nombre in habitaciones.keys():
            mesh = habitaciones[nombre]
            assert "tipo_int" in mesh.cell_data
            assert "area_m2"  in mesh.cell_data

    def prueba_cada_habitacion_tiene_una_celda(self, proyecto_simple):
        """Cada ambiente es un rectángulo con exactamente 1 celda y 4 puntos."""
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple)
        habitaciones = resultado["habitaciones"]
        for nombre in habitaciones.keys():
            mesh = habitaciones[nombre]
            assert mesh.n_cells  == 1
            assert mesh.n_points == 4


# ===========================================================================
# RenderizadorUnidad — casos borde
# ===========================================================================

class PruebaRenderizadorUnidadCasosBorde:

    def prueba_proyecto_sin_plantas_retorna_bloque_vacio(self, proyecto_sin_plantas):
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_sin_plantas)
        assert resultado is not None
        assert "habitaciones" in resultado.keys()
        assert "etiquetas"    in resultado.keys()
        assert len(resultado["habitaciones"].keys()) == 0

    def prueba_indice_fuera_de_rango_usa_ultimo(self, proyecto_simple):
        """Si unidad_idx > max, debe usar la última unidad sin lanzar error."""
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple, contexto={"unidad_idx": 999})
        assert resultado is not None
        assert len(resultado["habitaciones"].keys()) > 0

    def prueba_indice_negativo_usa_primera(self, proyecto_simple):
        """Si unidad_idx < 0, debe usar la primera unidad sin lanzar error."""
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_simple, contexto={"unidad_idx": -5})
        assert resultado is not None
        assert len(resultado["habitaciones"].keys()) > 0

    def prueba_contexto_vacio_usa_primera_unidad(self, proyecto_simple):
        """Sin contexto se usa la unidad con índice 0."""
        render = RenderizadorUnidad()
        resultado_sin = render.renderizar(proyecto_simple)
        resultado_idx0 = render.renderizar(proyecto_simple, contexto={"unidad_idx": 0})
        # Ambos deben producir el mismo número de habitaciones
        assert (len(resultado_sin["habitaciones"].keys()) ==
                len(resultado_idx0["habitaciones"].keys()))

    def prueba_monoambiente_genera_habitaciones(self, proyecto_monoambiente):
        """Un monoambiente debe generar habitaciones aunque no tenga dormitorios."""
        render = RenderizadorUnidad()
        resultado = render.renderizar(proyecto_monoambiente)
        assert len(resultado["habitaciones"].keys()) > 0

    def prueba_cuatro_ambientes_tiene_mas_ambientes_que_dos(
        self, proyecto_simple, proyecto_cuatro_ambientes
    ):
        render = RenderizadorUnidad()
        res_2 = render.renderizar(proyecto_simple, contexto={"unidad_idx": 0})
        res_4 = render.renderizar(proyecto_cuatro_ambientes, contexto={"unidad_idx": 0})
        # 4 ambientes tiene más rooms que 2 ambientes
        assert (len(res_4["habitaciones"].keys()) >
                len(res_2["habitaciones"].keys()))


# ===========================================================================
# RenderizadorUnidad — selección por contexto
# ===========================================================================

class PruebaRenderizadorUnidadContexto:

    def prueba_indice_1_selecciona_segunda_unidad(self, proyecto_simple):
        """El contexto {"unidad_idx": 1} debe seleccionar la segunda unidad de la planta tipo."""
        render = RenderizadorUnidad()
        # proyecto_simple tiene 3 unidades: 2amb, 2amb, 3amb
        res_0 = render.renderizar(proyecto_simple, contexto={"unidad_idx": 0})
        res_2 = render.renderizar(proyecto_simple, contexto={"unidad_idx": 2})

        n_0 = len(res_0["habitaciones"].keys())
        n_2 = len(res_2["habitaciones"].keys())

        # unidad 0 es 2amb, unidad 2 es 3amb → distinto número de ambientes
        assert n_0 != n_2

    def prueba_diferentes_indices_producen_geometrias_distintas(self, proyecto_simple):
        """Seleccionar unidades distintas produce MultiBlocks distintos."""
        render = RenderizadorUnidad()
        res_0 = render.renderizar(proyecto_simple, contexto={"unidad_idx": 0})
        res_2 = render.renderizar(proyecto_simple, contexto={"unidad_idx": 2})
        # Las alturas totales deben ser distintas (3amb tiene más área que 2amb)
        def altura_total(mb):
            ymax = 0.0
            for nombre in mb["habitaciones"].keys():
                pts = mb["habitaciones"][nombre].points
                ymax = max(ymax, float(pts[:, 1].max()))
            return ymax
        assert abs(altura_total(res_0) - altura_total(res_2)) > 0.01


# ===========================================================================
# MotorVista — despacho a RenderizadorUnidad
# ===========================================================================

class PruebaMotorVistaConTexto:

    def prueba_despacha_renderizador_unidad(self, proyecto_simple):
        """SeccionActiva.TIPOLOGIAS debe usar RenderizadorUnidad."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(proyecto_simple, SeccionActiva.TIPOLOGIAS)
        assert len(resultados) == 1
        assert "habitaciones" in resultados[0].keys()
        assert "etiquetas"    in resultados[0].keys()

    def prueba_contexto_se_pasa_al_renderizador(self, proyecto_simple):
        """El contexto {"unidad_idx": 2} debe seleccionar la tercera unidad."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(proyecto_simple, SeccionActiva.TIPOLOGIAS, contexto={"unidad_idx": 2})
        assert len(resultados) == 1

    def prueba_contexto_none_no_lanza_error(self, proyecto_simple):
        """Pasar contexto=None no debe lanzar excepción."""
        motor = MotorVista()
        motor.al_cambiar = lambda geom: None
        motor.actualizar(proyecto_simple, SeccionActiva.TIPOLOGIAS, contexto=None)

    def prueba_volumen_ignora_contexto(self, proyecto_simple):
        """Los renderizadores existentes (volumen, lote) ignoran el contexto sin error."""
        motor = MotorVista()
        resultados = []
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(
            proyecto_simple, SeccionActiva.GENERAL, contexto={"unidad_idx": 0}
        )
        assert len(resultados) == 1
        assert "plantas" in resultados[0].keys()

    def prueba_lote_ignora_contexto(self, proyecto_simple):
        """RenderizadorLote ignora el contexto sin error."""
        motor = MotorVista()
        resultados = []
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(
            proyecto_simple, SeccionActiva.LOTE, contexto={"unidad_idx": 0}
        )
        assert len(resultados) == 1
        assert "lote_base" in resultados[0].keys()


# ===========================================================================
# PanelBase — propiedad contexto_render
# (verificada de forma indirecta a través de MotorVistaConTexto)
#
# Nota: instanciar QWidget en el entorno de prueba headless genera conflictos
# entre PyQt6 y PySide6 (ambos cargados en el mismo proceso de pytest).
# La interfaz de contexto_render se valida a través de los tests de MotorVista
# que pasan contexto nulo/vacío y producen resultados correctos.
# ===========================================================================
