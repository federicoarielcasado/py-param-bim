# Mapa de Archivos — BIM Parametric Building Generator

> Este archivo se actualiza en cada sprint con los archivos nuevos o modificados.
> Es la referencia rápida para encontrar dónde está implementada cada funcionalidad.
> Última actualización: 16 de Marzo de 2026 | Versión: 0.4.0 (Fase 1 — Sprint 5: Panel Ambientes + Renderizador Ambientes 2D)

---

## Raíz del proyecto

| Archivo | Estado | Descripción |
|---|---|---|
| `main.py` | ✅ Funcional | **Punto de entrada.** Inicializa QApplication y abre VentanaPrincipal. Ejecutar con `python main.py`. |
| `requirements.txt` | ✅ Completo | Lista de dependencias Python. Instalar con `pip install -r requirements.txt`. |
| `ARCHIVOS.md` | ✅ Este archivo | Mapa de archivos del proyecto. Actualizar en cada sprint. |
| `pytest.ini` | ✅ Completo | Configuración de pytest para descubrir archivos de prueba en español (`prueba_*.py`, clases `Prueba*`, funciones `prueba_*`). |

---

## `bim_generador/` — Paquete principal

| Archivo | Estado | Descripción |
|---|---|---|
| `__init__.py` | ✅ | Versión del paquete y metadatos. |

---

## `bim_generador/nucleo/` — Motor central

| Archivo | Estado | Descripción |
|---|---|---|
| `motor_parametros.py` | ✅ **Implementado** | **Motor de parámetros principal.** Define la jerarquía completa de modelos Pydantic: `Proyecto → Lote → Edificio → Planta → Unidad → Ambiente`. Incluye campos computados, predeterminados por tipología, serialización JSON y métricas. Es el archivo más importante de la Fase 1. |
| `motor_reglas.py` | 🔲 Stub | Motor de reglas de diseño arquitectónico (`MotorReglas`). Aplica restricciones entre niveles. Planificado para Sprint 2-3. |
| `validador.py` | ✅ **Parcial** | Validador normativo (`Validador`) con soporte de perfiles por país. Implementa validación de FOS, FOT y superficies mínimas de ambientes. Carga perfiles desde `configuracion/normas/`. |

---

## `bim_generador/generadores/` — Generadores geométricos

| Archivo | Estado | Descripción |
|---|---|---|
| `arquitectonico.py` | 🔲 Stub | Genera muros, losas, aberturas, distribución de ambientes y unidades (`GeneradorArquitectonico`). Planificado para Fase 2. |
| `estructural.py` | 🔲 Stub | Genera la grilla de columnas y vigas (`GeneradorEstructural`). Planificado para Fase 2. |
| `circulacion.py` | 🔲 Stub | Genera núcleos verticales y pasillos (`GeneradorCirculacion`). Planificado para Fase 2. |
| `fachada.py` | 🔲 Stub | Genera fachadas y balcones (`GeneradorFachada`). Planificado para Fase 2. |

---

## `bim_generador/vista_previa/` — Motor de visualización

| Archivo | Estado | Descripción |
|---|---|---|
| `motor.py` | ✅ **Implementado** | Coordina los renderizadores según la `SeccionActiva` (`MotorVista`). Define el enum `SeccionActiva` con todas las secciones del RF-02. Expone `al_cambiar` como callback hacia la GUI. |
| `renderizadores/volumen.py` | ✅ **Implementado** | **Primer renderizador funcional.** Genera el volumen 3D del edificio como pyvista MultiBlock: plano de lote + boxes por planta (`RenderizadorVolumen`). |
| `renderizadores/lote.py` | ✅ **Implementado** | Vista 2D cenital del lote (`RenderizadorLote`). Genera 4 capas: `lote_base`, `zona_retiros`, `zona_edificable`, `cotas`. Disparado por `SeccionActiva.LOTE`. |
| `renderizadores/unidad.py` | ✅ **Implementado** | Planta esquemática 2D de una unidad funcional (`RenderizadorUnidad`). Layout por zonas: balcón/social/privado/servicios/circulación. Acepta `contexto={"unidad_idx": N}`. Disparado por `SeccionActiva.TIPOLOGIAS`. |
| `renderizadores/ambientes.py` | ✅ **Implementado** | Planta 2D con resaltado de ambiente seleccionado (`RenderizadorAmbientes`). Misma geometría que `RenderizadorUnidad` pero agrega `cell_data["seleccionado"]` y `cell_data["ambiente_orig_idx"]` a cada mesh. Acepta `contexto={"unidad_idx": N, "ambiente_idx": M}`. Disparado por `SeccionActiva.AMBIENTES`. |
| `renderizadores/estructura.py` | 🔲 Stub | Visualización de grilla estructural (`RenderizadorEstructura`). Planificado para Fase 2. |

---

## `bim_generador/interfaz/` — Interfaz gráfica (PyQt6)

| Archivo | Estado | Descripción |
|---|---|---|
| `ventana_principal.py` | ✅ **Implementado** | **Ventana principal** (`VentanaPrincipal`). Layout de 3 columnas: barra lateral de navegación + panel de configuración + vista previa 3D. |
| `widget_vista.py` | ✅ **Implementado** | Widget PyQt6 que embebe el plotter pyvista/VTK (`WidgetVista`). Despacha automáticamente entre modo 3D (volumen) y modo 2D cenital (lote) según las claves del MultiBlock recibido. |
| `paneles/panel_base.py` | ✅ **Implementado** | Clase base para todos los paneles (`PanelBase`). Define la señal `parametros_cambiados`, el método `cargar(proyecto)`, la property `seccion` y la property `contexto_render` (dict vacío por defecto, sobreescribible). |
| `paneles/panel_general.py` | ✅ **Implementado** | **Panel de parámetros generales** (`PanelGeneral`). Permite editar nombre, lote y edificio con métricas en tiempo real. |
| `paneles/panel_lote.py` | ✅ **Implementado** | Panel de Lote e Implantación (`PanelLote`). Edita dimensiones del lote, retiros y normativa. Muestra métricas de implantación con semáforo visual de cumplimiento FOS/FOT. |
| `paneles/panel_tipologias.py` | ✅ **Implementado** | Panel de Tipologías de Unidades (`PanelTipologias`). Lista editable de unidades por planta (combo+quitar), botón agregar, spinner de previsualización, métricas de planta tipo. Expone `contexto_render` con `{"unidad_idx": N}`. |
| `paneles/panel_ambientes.py` | ✅ **Implementado** | Panel de Edición de Ambientes (`PanelAmbientes`). Selección de unidad + ambiente, edición de superficie y ancho mínimo, validación normativa inline con semáforo verde/amarillo/rojo, métricas de unidad. Expone `contexto_render` con `{"unidad_idx": N, "ambiente_idx": M}`. |
| `paneles/panel_unidad.py` | 🔲 Stub | Stub vacío (reemplazado por `panel_ambientes.py`). |
| `paneles/panel_circulacion.py` | 🔲 Stub | Panel de Circulación (`PanelCirculacion`). Planificado para Fase 2. |
| `paneles/panel_estructura.py` | 🔲 Stub | Panel de Estructura (`PanelEstructura`). Planificado para Fase 2. |
| `paneles/panel_fachada.py` | 🔲 Stub | Panel de Fachada (`PanelFachada`). Planificado para Fase 2. |
| `paneles/panel_materiales.py` | 🔲 Stub | Panel de Materiales (`PanelMateriales`). Planificado para Fase 2. |
| `paneles/panel_documentacion.py` | 🔲 Stub | Panel de Documentación (`PanelDocumentacion`). Planificado para Fase 2. |

---

## `bim_generador/revit/` — Integración Revit

| Archivo | Estado | Descripción |
|---|---|---|
| `exportador.py` | 🔲 Stub | Capa de abstracción sobre la API de Revit (`ExportadorRevit`). Planificado para Fase 3 (Sprint 8-10). |
| `fabrica_elementos.py` | 🔲 Stub | Fábrica de elementos Revit. Planificado para Fase 3. |

---

## `bim_generador/configuracion/` — Configuración externa

| Archivo | Estado | Descripción |
|---|---|---|
| `normas/argentina_caba.json` | ✅ **Completo** | Perfil normativo Argentina — Código Urbano CABA. Contiene: FOS/FOT máximos, retiros mínimos, superficies mínimas por ambiente, parámetros de circulación, iluminación y ventilación. |
| `tipologias/residential.yaml` | ✅ **Completo** | Biblioteca de tipologías de departamentos residenciales. |

---

## `bim_generador/reportes/` — Reportes

| Archivo | Estado | Descripción |
|---|---|---|
| `generador.py` | 🔲 Stub | Genera reportes en PDF y Excel (`GeneradorReporte`). Planificado para Fase 3. |

---

## `pruebas/` — Pruebas

| Archivo | Estado | Descripción |
|---|---|---|
| `prueba_motor_parametros.py` | ✅ **Implementado** | Pruebas del motor de parámetros. Cubre: Ambiente, Unidad, Planta, Lote, Edificio, Proyecto. Incluye pruebas de campos computados, predeterminados y roundtrip JSON. |
| `prueba_validador.py` | ✅ **Implementado** | Pruebas del validador normativo. Cubre carga de perfil, validación FOS/FOT y superficies mínimas. |
| `prueba_renderizadores.py` | ✅ **Implementado** | Pruebas de los renderizadores de vista previa. Cubre: `RenderizadorVolumen` (claves, geometría, retiros), `RenderizadorLote` (capas, dimensiones, casos borde) y `MotorVista` (despacho por sección, compatibilidad con contexto). |
| `prueba_tipologias.py` | ✅ **Implementado** | Pruebas del Sprint 4. Cubre: `RenderizadorUnidad` (claves, habitaciones, etiquetas tipo_int/area_m2, casos borde), selección por contexto y `MotorVista` con contexto. |
| `prueba_ambientes.py` | ✅ **Implementado** | Pruebas del Sprint 5. Cubre: `RenderizadorAmbientes` (estructura MultiBlock, cell_data, invariante exactamente-uno-seleccionado, casos borde con índices fuera de rango) y `MotorVista` con `SeccionActiva.AMBIENTES`. |

---

## Leyenda de estados

| Ícono | Significado |
|---|---|
| ✅ **Implementado** | Funcional y testeado |
| ✅ **Parcial** | Implementado con funcionalidad básica; pendiente de completar |
| 🔲 Stub | Interfaz definida, implementación pendiente según roadmap |

---

## Árbol de directorios

```
py-param-bim/
├── main.py                              # Punto de entrada
├── requirements.txt
├── pytest.ini                           # Configuración de pytest en español
├── ARCHIVOS.md                          # Este archivo
└── bim_generador/
    ├── __init__.py
    ├── nucleo/
    │   ├── motor_parametros.py          ← Implementado ✅
    │   ├── motor_reglas.py              ← Stub
    │   └── validador.py                 ← Parcial ✅
    ├── generadores/
    │   ├── arquitectonico.py            ← Stub
    │   ├── estructural.py               ← Stub
    │   ├── circulacion.py               ← Stub
    │   └── fachada.py                   ← Stub
    ├── vista_previa/
    │   ├── motor.py                     ← Implementado ✅
    │   └── renderizadores/
    │       ├── volumen.py               ← Implementado ✅
    │       ├── lote.py                  ← Implementado ✅
    │       ├── unidad.py                ← Implementado ✅
    │       ├── ambientes.py             ← Implementado ✅
    │       └── estructura.py            ← Stub
    ├── revit/
    │   ├── exportador.py                ← Stub (Fase 3)
    │   └── fabrica_elementos.py         ← Stub (Fase 3)
    ├── interfaz/
    │   ├── ventana_principal.py         ← Implementado ✅
    │   ├── widget_vista.py              ← Implementado ✅
    │   └── paneles/
    │       ├── panel_base.py            ← Implementado ✅
    │       ├── panel_general.py         ← Implementado ✅
    │       ├── panel_lote.py            ← Implementado ✅
    │       ├── panel_tipologias.py      ← Implementado ✅
    │       ├── panel_ambientes.py       ← Implementado ✅
    │       ├── panel_unidad.py          ← Stub
    │       ├── panel_circulacion.py     ← Stub
    │       ├── panel_estructura.py      ← Stub
    │       ├── panel_fachada.py         ← Stub
    │       ├── panel_materiales.py      ← Stub
    │       └── panel_documentacion.py   ← Stub
    ├── configuracion/
    │   ├── normas/
    │   │   └── argentina_caba.json      ← Completo ✅
    │   └── tipologias/
    │       └── residential.yaml         ← Completo ✅
    ├── reportes/
    │   └── generador.py                 ← Stub (Fase 3)
└── pruebas/
    ├── prueba_motor_parametros.py       ← Implementado ✅
    ├── prueba_validador.py              ← Implementado ✅
    ├── prueba_renderizadores.py         ← Implementado ✅
    ├── prueba_tipologias.py             ← Implementado ✅
    └── prueba_ambientes.py              ← Implementado ✅
```
