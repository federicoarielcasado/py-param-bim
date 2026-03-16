"""
prueba_ambientes.py
-------------------
Pruebas del Sprint 5 — Edición de Ambientes y RenderizadorAmbientes.

Cubre:
  - RenderizadorAmbientes: estructura del MultiBlock (claves, cell_data)
  - RenderizadorAmbientes: flag seleccionado en cada ambiente
  - RenderizadorAmbientes: exactamente un ambiente seleccionado por render
  - RenderizadorAmbientes: contexto unidad_idx + ambiente_idx
  - RenderizadorAmbientes: casos borde (sin plantas, índices fuera de rango)
  - tipo_vista() devuelve "ambientes_2d"
  - MotorVista despacha correctamente a RenderizadorAmbientes (SeccionActiva.AMBIENTES)

Ejecutar con:
    pytest pruebas/prueba_ambientes.py -v
"""

import pytest

from bim_generador.nucleo.motor_parametros              import (
    Proyecto, TipoUnidad, TipoAmbiente, Unidad, Ambiente, TipoPlanta,
)
from bim_generador.vista_previa.motor                   import MotorVista, SeccionActiva
from bim_generador.vista_previa.renderizadores.ambientes import RenderizadorAmbientes


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def proyecto_std():
    """Proyecto estándar con mix de 2amb, 2amb, 3amb."""
    return Proyecto.desde_predeterminados("Test Amb")


@pytest.fixture
def proyecto_mono():
    """Proyecto con monoambientes (sin dormitorios)."""
    p = Proyecto.desde_predeterminados("Mono")
    p.edificio.generar_plantas_tipo([
        Unidad.desde_tipologia(TipoUnidad.MONOAMBIENTE, codigo="A"),
    ])
    return p


@pytest.fixture
def proyecto_4amb():
    """Proyecto con unidades de 4 ambientes."""
    p = Proyecto.desde_predeterminados("4amb")
    p.edificio.generar_plantas_tipo([
        Unidad.desde_tipologia(TipoUnidad.CUATRO_AMBIENTES, codigo="A"),
    ])
    return p


@pytest.fixture
def proyecto_sin_plantas():
    """Proyecto con lista de plantas vacía."""
    p = Proyecto.desde_predeterminados("Vacio")
    p.edificio.plantas = []
    return p


# ===========================================================================
# RenderizadorAmbientes — estructura básica
# ===========================================================================

class PruebaRenderizadorAmbientes:

    def prueba_retorna_multiblock(self, proyecto_std):
        import pyvista as pv
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        assert resultado is not None
        assert isinstance(resultado, pv.MultiBlock)

    def prueba_clave_habitaciones_amb(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        assert "habitaciones_amb" in resultado.keys()

    def prueba_clave_etiquetas(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        assert "etiquetas" in resultado.keys()

    def prueba_habitaciones_no_vacias(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        assert len(resultado["habitaciones_amb"].keys()) > 0

    def prueba_tipo_vista_es_ambientes_2d(self):
        assert RenderizadorAmbientes.tipo_vista() == "ambientes_2d"

    def prueba_cada_mesh_tiene_tipo_int(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        for nombre in resultado["habitaciones_amb"].keys():
            mesh = resultado["habitaciones_amb"][nombre]
            assert "tipo_int" in mesh.cell_data

    def prueba_cada_mesh_tiene_area_m2(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        for nombre in resultado["habitaciones_amb"].keys():
            mesh = resultado["habitaciones_amb"][nombre]
            assert "area_m2" in mesh.cell_data

    def prueba_cada_mesh_tiene_flag_seleccionado(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        for nombre in resultado["habitaciones_amb"].keys():
            mesh = resultado["habitaciones_amb"][nombre]
            assert "seleccionado" in mesh.cell_data

    def prueba_cada_mesh_tiene_ambiente_orig_idx(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        for nombre in resultado["habitaciones_amb"].keys():
            mesh = resultado["habitaciones_amb"][nombre]
            assert "ambiente_orig_idx" in mesh.cell_data

    def prueba_cantidad_habitaciones_igual_ambientes(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        planta_tipo = next(
            p for p in proyecto_std.edificio.plantas
            if p.tipo_planta == TipoPlanta.PLANTA_TIPO
        )
        n_amb = len(planta_tipo.unidades[0].ambientes)
        assert len(resultado["habitaciones_amb"].keys()) == n_amb


# ===========================================================================
# RenderizadorAmbientes — flag seleccionado
# ===========================================================================

class PruebaSeleccionado:

    def prueba_exactamente_un_seleccionado_por_defecto(self, proyecto_std):
        """Sin contexto, exactamente 1 ambiente debe tener seleccionado=1."""
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        n_sel = sum(
            int(resultado["habitaciones_amb"][n].cell_data["seleccionado"][0])
            for n in resultado["habitaciones_amb"].keys()
        )
        assert n_sel == 1

    def prueba_exactamente_un_seleccionado_con_contexto(self, proyecto_std):
        """Con ambiente_idx explícito, sigue habiendo exactamente 1 seleccionado."""
        render = RenderizadorAmbientes()
        for idx in range(3):
            resultado = render.renderizar(proyecto_std, contexto={"ambiente_idx": idx})
            n_sel = sum(
                int(resultado["habitaciones_amb"][n].cell_data["seleccionado"][0])
                for n in resultado["habitaciones_amb"].keys()
            )
            assert n_sel == 1, f"ambiente_idx={idx} produjo {n_sel} seleccionados"

    def prueba_primero_seleccionado_sin_contexto(self, proyecto_std):
        """Sin contexto, el ambiente con ambient_orig_idx=0 debe estar seleccionado."""
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        for nombre in resultado["habitaciones_amb"].keys():
            mesh = resultado["habitaciones_amb"][nombre]
            orig_idx = int(mesh.cell_data["ambiente_orig_idx"][0])
            es_sel   = int(mesh.cell_data["seleccionado"][0])
            if orig_idx == 0:
                assert es_sel == 1, "El ambiente de índice 0 debería estar seleccionado"

    def prueba_ambiente_idx_2_selecciona_tercero(self, proyecto_std):
        """contexto ambiente_idx=2 debe seleccionar el ambiente con orig_idx=2."""
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std, contexto={"ambiente_idx": 2})
        for nombre in resultado["habitaciones_amb"].keys():
            mesh = resultado["habitaciones_amb"][nombre]
            orig_idx = int(mesh.cell_data["ambiente_orig_idx"][0])
            es_sel   = int(mesh.cell_data["seleccionado"][0])
            if orig_idx == 2:
                assert es_sel == 1
            else:
                assert es_sel == 0

    def prueba_etiquetas_tienen_flag_seleccionado(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        etiq = resultado["etiquetas"]
        assert "seleccionado" in etiq.point_data

    def prueba_etiquetas_una_seleccionada(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        etiq = resultado["etiquetas"]
        n_sel = int(sum(etiq.point_data["seleccionado"]))
        assert n_sel == 1

    def prueba_flag_seleccionado_es_0_o_1(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std)
        for nombre in resultado["habitaciones_amb"].keys():
            val = int(resultado["habitaciones_amb"][nombre].cell_data["seleccionado"][0])
            assert val in (0, 1)


# ===========================================================================
# RenderizadorAmbientes — casos borde
# ===========================================================================

class PruebaRenderizadorAmbientesCasosBorde:

    def prueba_sin_plantas_retorna_bloque_vacio(self, proyecto_sin_plantas):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_sin_plantas)
        assert resultado is not None
        assert len(resultado["habitaciones_amb"].keys()) == 0

    def prueba_ambiente_idx_fuera_de_rango_usa_ultimo(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std, contexto={"ambiente_idx": 999})
        assert resultado is not None
        n_sel = sum(
            int(resultado["habitaciones_amb"][n].cell_data["seleccionado"][0])
            for n in resultado["habitaciones_amb"].keys()
        )
        assert n_sel == 1

    def prueba_unidad_idx_fuera_de_rango_usa_ultima(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std, contexto={"unidad_idx": 999})
        assert resultado is not None
        assert len(resultado["habitaciones_amb"].keys()) > 0

    def prueba_contexto_none_no_lanza_error(self, proyecto_std):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_std, contexto=None)
        assert resultado is not None

    def prueba_monoambiente_tiene_un_seleccionado(self, proyecto_mono):
        render = RenderizadorAmbientes()
        resultado = render.renderizar(proyecto_mono)
        n_sel = sum(
            int(resultado["habitaciones_amb"][n].cell_data["seleccionado"][0])
            for n in resultado["habitaciones_amb"].keys()
        )
        assert n_sel == 1

    def prueba_4_ambientes_mas_meshes_que_2(self, proyecto_std, proyecto_4amb):
        render = RenderizadorAmbientes()
        res_2 = render.renderizar(proyecto_std)
        res_4 = render.renderizar(proyecto_4amb)
        assert (len(res_4["habitaciones_amb"].keys()) >
                len(res_2["habitaciones_amb"].keys()))


# ===========================================================================
# MotorVista — despacho a RenderizadorAmbientes
# ===========================================================================

class PruebaMotorVistaAmbientes:

    def prueba_despacha_renderizador_ambientes(self, proyecto_std):
        """SeccionActiva.AMBIENTES debe producir clave 'habitaciones_amb'."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda g: resultados.append(g)
        motor.actualizar(proyecto_std, SeccionActiva.AMBIENTES)
        assert len(resultados) == 1
        assert "habitaciones_amb" in resultados[0].keys()

    def prueba_contexto_ambiente_idx_se_aplica(self, proyecto_std):
        """El contexto {"ambiente_idx": 2} debe seleccionar el tercero."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda g: resultados.append(g)
        motor.actualizar(proyecto_std, SeccionActiva.AMBIENTES,
                         contexto={"unidad_idx": 0, "ambiente_idx": 2})
        assert len(resultados) == 1
        # Verificar que el ambiente con orig_idx=2 está seleccionado
        hab = resultados[0]["habitaciones_amb"]
        for nombre in hab.keys():
            mesh = hab[nombre]
            if int(mesh.cell_data["ambiente_orig_idx"][0]) == 2:
                assert int(mesh.cell_data["seleccionado"][0]) == 1
                break

    def prueba_otros_renderizadores_siguen_funcionando(self, proyecto_std):
        """Agregar AMBIENTES no debe romper GENERAL, LOTE ni TIPOLOGIAS."""
        motor = MotorVista()
        resultados = {}

        for seccion in (SeccionActiva.GENERAL, SeccionActiva.LOTE, SeccionActiva.TIPOLOGIAS):
            res = []
            motor.al_cambiar = lambda g, s=seccion: res.append(g)
            motor.actualizar(proyecto_std, seccion)
            resultados[seccion] = res

        assert "plantas"         in resultados[SeccionActiva.GENERAL][0].keys()
        assert "lote_base"       in resultados[SeccionActiva.LOTE][0].keys()
        assert "habitaciones"    in resultados[SeccionActiva.TIPOLOGIAS][0].keys()
