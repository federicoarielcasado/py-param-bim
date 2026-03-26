"""
prueba_renderizadores.py
------------------------
Pruebas de los renderizadores de vista previa.

Cubre:
  - RenderizadorVolumen: claves del MultiBlock, geometría válida
  - RenderizadorLote: capas generadas, geometría válida ante distintos retiros
  - MotorVista: despacho correcto según SeccionActiva

Ejecutar con:
    pytest pruebas/prueba_renderizadores.py -v
"""

import pytest
import numpy as np

from bim_generador.nucleo.motor_parametros             import Proyecto, TipoUnidad, Unidad
from bim_generador.vista_previa.motor                  import MotorVista, SeccionActiva
from bim_generador.vista_previa.renderizadores.volumen import RenderizadorVolumen
from bim_generador.vista_previa.renderizadores.lote    import RenderizadorLote


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def proyecto_simple():
    """Proyecto con lote 20×40 m, 5 pisos, 2 unidades por planta."""
    p = Proyecto.desde_predeterminados("Test Render")
    p.lote.frente_m = 20.0
    p.lote.fondo_m  = 40.0
    p.edificio.cantidad_pisos = 5
    # Regenerar plantas para reflejar la nueva cantidad de pisos
    unidades_tipo = p.edificio.plantas[0].unidades if p.edificio.plantas else []
    p.edificio.generar_plantas_tipo(unidades_tipo)
    return p


@pytest.fixture
def proyecto_sin_retiros():
    """Proyecto con retiros en cero (caso límite)."""
    p = Proyecto.desde_predeterminados("Sin Retiros")
    p.edificio.retiro_frontal_m   = 0.0
    p.edificio.retiro_lateral_m   = 0.0
    p.edificio.retiro_posterior_m = 0.0
    return p


@pytest.fixture
def proyecto_retiros_excesivos():
    """Proyecto cuyos retiros suman más que el lote (caso borde)."""
    p = Proyecto.desde_predeterminados("Retiros Grandes")
    p.lote.frente_m = 10.0
    p.lote.fondo_m  = 10.0
    p.edificio.retiro_lateral_m   = 6.0   # 6 + 6 = 12 > 10
    p.edificio.retiro_frontal_m   = 6.0
    p.edificio.retiro_posterior_m = 6.0
    return p


# ===========================================================================
# RenderizadorVolumen
# ===========================================================================

class PruebaRenderizadorVolumen:

    def prueba_retorna_multiblock(self, proyecto_simple):
        import pyvista as pv
        render = RenderizadorVolumen()
        resultado = render.renderizar(proyecto_simple)
        assert resultado is not None
        assert isinstance(resultado, pv.MultiBlock)

    def prueba_clave_lote_presente(self, proyecto_simple):
        render = RenderizadorVolumen()
        resultado = render.renderizar(proyecto_simple)
        assert "lote" in resultado.keys()

    def prueba_clave_plantas_presente(self, proyecto_simple):
        render = RenderizadorVolumen()
        resultado = render.renderizar(proyecto_simple)
        assert "plantas" in resultado.keys()

    def prueba_cantidad_plantas_correcta(self, proyecto_simple):
        render = RenderizadorVolumen()
        resultado = render.renderizar(proyecto_simple)
        plantas_block = resultado["plantas"]
        # 5 pisos + PB = 6 plantas
        assert len(plantas_block.keys()) == 6

    def prueba_lote_tiene_puntos(self, proyecto_simple):
        render = RenderizadorVolumen()
        resultado = render.renderizar(proyecto_simple)
        assert resultado["lote"].n_points == 4

    def prueba_retiros_excesivos_genera_bloque_vacio(self, proyecto_retiros_excesivos):
        render = RenderizadorVolumen()
        resultado = render.renderizar(proyecto_retiros_excesivos)
        # Si los retiros exceden el lote, plantas debe estar vacío
        plantas_block = resultado["plantas"]
        assert len(plantas_block.keys()) == 0


# ===========================================================================
# RenderizadorLote
# ===========================================================================

class PruebaRenderizadorLote:

    def prueba_retorna_multiblock(self, proyecto_simple):
        import pyvista as pv
        render = RenderizadorLote()
        resultado = render.renderizar(proyecto_simple)
        assert resultado is not None
        assert isinstance(resultado, pv.MultiBlock)

    def prueba_claves_presentes(self, proyecto_simple):
        render = RenderizadorLote()
        resultado = render.renderizar(proyecto_simple)
        claves = resultado.keys()
        assert "lote_base" in claves
        assert "zona_retiros" in claves
        assert "zona_edificable" in claves
        assert "cotas" in claves

    def prueba_lote_base_dimension_correcta(self, proyecto_simple):
        """El polígono del lote debe cubrir exactamente frente × fondo."""
        render = RenderizadorLote()
        resultado = render.renderizar(proyecto_simple)
        pts = resultado["lote_base"].points
        xmax = float(pts[:, 0].max())
        ymax = float(pts[:, 1].max())
        assert abs(xmax - proyecto_simple.lote.frente_m) < 0.001
        assert abs(ymax - proyecto_simple.lote.fondo_m) < 0.001

    def prueba_sin_retiros_zona_retiros_vacia(self, proyecto_sin_retiros):
        render = RenderizadorLote()
        resultado = render.renderizar(proyecto_sin_retiros)
        # Con retiros = 0, el mesh de retiros debe tener 0 celdas
        assert resultado["zona_retiros"].n_cells == 0

    def prueba_retiros_excesivos_zona_edificable_vacia(self, proyecto_retiros_excesivos):
        render = RenderizadorLote()
        resultado = render.renderizar(proyecto_retiros_excesivos)
        assert resultado["zona_edificable"].n_cells == 0

    def prueba_tipo_vista_es_lote_2d(self):
        assert RenderizadorLote.tipo_vista() == "lote_2d"

    def prueba_cotas_tienen_lineas(self, proyecto_simple):
        render = RenderizadorLote()
        resultado = render.renderizar(proyecto_simple)
        # Las cotas deben tener al menos las 2 líneas principales + 4 ticks
        assert resultado["cotas"].n_cells >= 6


# ===========================================================================
# MotorVista
# ===========================================================================

class PruebaMotorVista:

    def prueba_despacha_renderizador_volumen(self, proyecto_simple):
        """SeccionActiva.GENERAL debe usar RenderizadorVolumen."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(proyecto_simple, SeccionActiva.GENERAL)
        assert len(resultados) == 1
        assert "lote" in resultados[0].keys()
        assert "plantas" in resultados[0].keys()

    def prueba_despacha_renderizador_lote(self, proyecto_simple):
        """SeccionActiva.LOTE debe usar RenderizadorLote."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(proyecto_simple, SeccionActiva.LOTE)
        assert len(resultados) == 1
        assert "lote_base" in resultados[0].keys()

    def prueba_estructura_llama_callback(self, proyecto_simple):
        """SeccionActiva.ESTRUCTURA debe usar RenderizadorEstructura (Sprint 6)."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(proyecto_simple, SeccionActiva.ESTRUCTURA)
        assert len(resultados) == 1
        assert "grilla_estructura" in resultados[0].keys()

    def prueba_circulacion_llama_callback(self, proyecto_simple):
        """SeccionActiva.CIRCULACION debe usar RenderizadorCirculacion (Sprint 6)."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(proyecto_simple, SeccionActiva.CIRCULACION)
        assert len(resultados) == 1
        assert "planta_circulacion" in resultados[0].keys()

    def prueba_seccion_sin_renderizador_no_llama_callback(self, proyecto_simple):
        """Secciones sin renderizador implementado no deben llamar al callback."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        # MATERIALES todavía no tiene renderizador (Fase 2)
        motor.actualizar(proyecto_simple, SeccionActiva.MATERIALES)
        assert len(resultados) == 0

    def prueba_sin_callback_no_lanza_error(self, proyecto_simple):
        """El motor sin callback asignado no debe lanzar excepción."""
        motor = MotorVista()
        motor.actualizar(proyecto_simple, SeccionActiva.GENERAL)  # no debe lanzar

    def prueba_actualizar_dos_veces_mismo_proyecto(self, proyecto_simple):
        """Actualizar dos veces debe producir dos resultados independientes."""
        resultados = []
        motor = MotorVista()
        motor.al_cambiar = lambda geom: resultados.append(geom)
        motor.actualizar(proyecto_simple, SeccionActiva.GENERAL)
        motor.actualizar(proyecto_simple, SeccionActiva.LOTE)
        assert len(resultados) == 2
