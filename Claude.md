# Claude.md — BIM Parametric Building Generator

> **Documento de contexto de largo plazo para agentes de IA.**
> Versión: 1.0 | Fecha: 2026-03-13 | Autor: Fede
> Este archivo es la fuente de verdad del proyecto. Actualizar ante cambios de alcance, decisiones de arquitectura o nuevos sprints.

---

## 0) Meta y Contexto General

**Nombre del sistema:** BIM Parametric Building Generator
**Dominio:** Automatización BIM · Diseño paramétrico · Ingeniería Civil aplicada

### ¿Qué es?
Herramienta de escritorio (Windows) para generar automáticamente modelos BIM de edificios residenciales en Autodesk Revit, a partir de parámetros configurables por el usuario. El sistema incluye una interfaz de configuración con preview geométrica contextual independiente de Revit, y un pipeline de exportación hacia el modelo BIM final.

### Contexto del desarrollador
- Ingeniero Civil con experiencia en Python, finanzas e ingeniería estructural.
- Sin experiencia previa con la API de Revit ni Dynamo → curva de aprendizaje incluida en el plan.
- Proyecto personal/portfolio con proyección a producto escalable.

### Filosofía de diseño de interfaz
Inspirada en tres referencias:
- **Autodesk Forma** → exploración volumétrica temprana, simplicidad analítica.
- **The Sims** → construcción modular intuitiva, edición directa de ambientes.
- **Speckle** → visualización técnica limpia orientada a BIM.

El principio central: **preview inmediato y contextual** — el nivel de detalle del visualizador cambia según qué sección de parámetros está editando el usuario.

### Stack tecnológico definido
| Capa | Tecnología |
|---|---|
| GUI | PyQt6 o PySide6 |
| Preview geométrica | OpenGL via PyOpenGL / VTK / matplotlib 3D (a evaluar) |
| Motor paramétrico | Python puro + dataclasses/Pydantic |
| Configuración | JSON / YAML / Excel (.xlsx) |
| Integración BIM | pyRevit + API de Revit (RPW o clr) |
| Validación normativa | Módulo Python configurable por perfil de país |

---

## 1) Objetivos SMART

| ID | Objetivo | Métrica | Plazo |
|---|---|---|---|
| O1 | Implementar interfaz de configuración paramétrica con preview contextual funcional | Preview responde en < 2 seg ante cambio de parámetro | Sprint 1-3 |
| O2 | Generar planta tipo de edificio residencial válida automáticamente | Cumple reglas mínimas de circulación, ventilación y superficie | Sprint 4-6 |
| O3 | Exportar modelo básico a Revit (muros, losas, columnas) desde los parámetros | Modelo se abre en Revit sin errores críticos | Sprint 7-9 |
| O4 | Validar normativamente diseños contra CIRSOC y código urbano de CABA/GBA | Reporte de incumplimientos generado automáticamente | Sprint 8-10 |
| O5 | Generar variantes comparables del edificio (optimización) | Al menos 3 variantes comparadas por métricas de eficiencia | Backlog |

---

## 2) Alcance y Exclusiones

### Dentro del alcance (MVP y siguientes fases)
- Edificios residenciales de vivienda colectiva (PB + N plantas tipo + último piso).
- Configuración de: lote, volumen, tipologías de departamentos, circulación, estructura básica, fachadas, materiales.
- Preview geométrica simplificada (no renderizado, geometría básica).
- Exportación a Revit: muros, losas, columnas, vigas, aberturas.
- Validación normativa con perfil Argentina (CIRSOC 201, código urbano).
- Reportes de superficie, unidades y métricas básicas del proyecto.
- Arquitectura modular preparada para escalar.

### Fuera del alcance (por ahora)
- Instalaciones MEP (sanitaria, eléctrica, HVAC).
- Renders fotorrealistas o visualización avanzada.
- Cálculo estructural detallado (solo geometría estructural básica).
- Integración con presupuestación o software de obra.
- Multi-usuario / colaboración en tiempo real.
- Soporte multi-tipología (oficinas, comercial) en etapa inicial.
- Normativas de otros países (se diseña para extensión futura).

---

## 3) Requisitos Detallados

### Funcionales (RF)

**RF-01 — Motor de parámetros**
El sistema debe aceptar parámetros de entrada organizados jerárquicamente:
```
Proyecto → Lote → Edificio → Planta → Unidad → Ambiente
```
Cada nivel tiene parámetros propios. Cambios en niveles superiores propagan restricciones hacia abajo.

**RF-02 — Preview contextual**
La visualización cambia automáticamente según la sección activa:
| Sección activa | Preview |
|---|---|
| Parámetros generales | Volumen 3D del edificio |
| Lote / implantación | Vista superior con polígono de lote |
| Tipologías de departamento | Planta interactiva de unidad |
| Ambientes | Distribución interior del departamento |
| Circulación | Planta del piso con núcleos y pasillos |
| Estructura | Grilla estructural con columnas y vigas |
| Fachada | Vista 3D frontal del edificio |
| Materiales | Muestras visuales de materiales |
| Documentación | Preview de plano simplificado |

**RF-03 — Generador arquitectónico**
Debe generar automáticamente: muros perimetrales e interiores, losas, aberturas (puertas y ventanas), balcones, núcleos verticales (caja de escalera + ascensor), pasillos de distribución.

**RF-04 — Validador normativo**
Debe verificar, como mínimo:
- Superficie mínima por ambiente (según código urbano)
- Factor de ocupación del suelo (FOS) y factor de ocupación total (FOT)
- Distancia máxima de evacuación a núcleo vertical
- Ventilación e iluminación natural de ambientes habitables
- Módulo estructural básico compatible con CIRSOC 201

**RF-05 — Exportación a Revit**
El sistema debe poder crear elementos en un archivo Revit (.rvt) via pyRevit o la API de Revit:
muros, losas, columnas, vigas, puertas, ventanas. El flujo debe ser reproducible y parametrizado.

**RF-06 — Reportes**
Generar reporte en PDF o Excel con: superficie por unidad, superficie total por planta, cantidad de unidades por tipología, métricas de eficiencia (ratio circulación/vendible).

### No Funcionales (RNF)

| ID | Requisito | Criterio |
|---|---|---|
| RNF-01 | Rendimiento de preview | Regeneración en < 2 segundos ante cambio de parámetro |
| RNF-02 | Arquitectura modular | Cada módulo reemplazable independientemente |
| RNF-03 | Configuración externa | Toda normativa y tipología en archivos JSON/YAML (sin hardcodear) |
| RNF-04 | Compatibilidad | Windows 10/11, Revit 2022+ |
| RNF-05 | Extensibilidad normativa | Agregar nuevo perfil de país sin modificar código core |
| RNF-06 | Trazabilidad | Todo elemento generado en Revit tiene parámetro de origen identificable |

---

## 4) Casos de Uso Principales

**CU-01: Configurar nuevo edificio desde cero**
Actor: Usuario. Flujo: selecciona tipología de lote → define volumen → elige tipologías de departamentos → configura estructura → previsualiza → exporta a Revit.

**CU-02: Modificar tipología de departamento y ver impacto**
Actor: Usuario. Flujo: abre configuración de unidad tipo 2 ambientes → modifica superficie del living → el sistema regenera la planta y valida superficies mínimas → muestra advertencias si hay incumplimientos.

**CU-03: Generar y comparar variantes**
Actor: Usuario. Flujo: define objetivo de optimización (maximizar unidades) → el sistema genera N variantes modificando distribución → presenta tabla comparativa de métricas → usuario selecciona variante preferida.

**CU-04: Exportar modelo a Revit**
Actor: Usuario. Flujo: revisa preview final → confirma exportación → el sistema ejecuta script de generación via API de Revit → modelo se abre en Revit con todos los elementos etiquetados.

**CU-05: Validar normativa**
Actor: Sistema (automático). Flujo: ante cada cambio relevante, el validador corre en background → lista de advertencias/errores aparece en panel lateral → usuario puede ignorar o corregir.

---

## 5) Stakeholders y Roles

| Rol | Descripción |
|---|---|
| **Desarrollador / Usuario principal** | Fede — diseña, implementa y usa la herramienta |
| **Usuario secundario (futuro)** | Arquitectos o estudios que adopten la herramienta |
| **Agente de IA (Claude)** | Co-desarrollador: generación de código, revisión de arquitectura, planificación de sprints |
| **Revit (sistema externo)** | Receptor del modelo generado; no es interactivo durante la generación |

---

## 6) Supuestos, Riesgos y Mitigaciones

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | Curva de aprendizaje de la API de Revit es alta | Alta | Alto | Comenzar con pyRevit (más accesible); reservar sprints de aprendizaje; usar ejemplos de la comunidad |
| R2 | La preview geométrica resulta lenta para edificios complejos | Media | Medio | Usar geometría simplificada (bounding boxes); LOD progresivo según zoom |
| R3 | Conflicto entre reglas de diseño (ej: máximos de FOT vs cantidad de unidades) | Alta | Medio | Implementar sistema de prioridades en el validador; alertas no bloqueantes |
| R4 | La API de Revit cambia entre versiones | Baja | Alto | Abstraer capa de integración Revit en módulo aislado |
| R5 | Scope creep: el sistema crece sin foco claro | Alta | Alto | Mantener este Claude.md actualizado; definir criterios de "done" por sprint |

**Supuestos del proyecto:**
- El usuario tiene Revit 2022+ instalado con licencia activa.
- El sistema corre en Windows 10/11 con Python 3.10+.
- Las normativas de referencia son las vigentes al inicio del proyecto (CIRSOC 201-2005, Código Urbano CABA).
- El motor de preview NO necesita ser fotorrealista, solo funcional y claro.

---

## 7) Entregables y Cronograma Sugerido

> Cronograma orientativo. Sin fechas fijas; se organiza en sprints de 1-2 semanas.

### Fase 1 — Fundamentos e Interfaz (Sprints 1-4)
- [ ] Arquitectura de módulos definida y documentada
- [ ] Motor de parámetros con jerarquía Proyecto→Lote→Edificio→Planta→Unidad
- [ ] GUI básica en PyQt6/PySide6 con paneles de configuración
- [ ] Preview geométrica simple: volumen 3D del edificio (matplotlib 3D o VTK)
- [ ] Archivos de configuración JSON para tipologías de departamentos

### Fase 2 — Generación Arquitectónica (Sprints 5-7)
- [ ] Generador de planta tipo: muros, circulación, núcleos, unidades
- [ ] Preview contextual completa (todas las secciones del RF-02)
- [ ] Validador normativo básico (superficies, FOS/FOT, evacuación)
- [ ] Biblioteca de tipologías de departamentos (1, 2 y 3 ambientes)

### Fase 3 — Integración Revit (Sprints 8-10)
- [ ] Aprendizaje y prototipo de API de Revit (pyRevit)
- [ ] Exportador de muros y losas a Revit
- [ ] Exportador completo: columnas, vigas, aberturas, etiquetas
- [ ] Reporte básico de superficies (PDF/Excel)

### Fase 4 — Optimización y Escalado (Backlog)
- [ ] Motor de variantes y comparación
- [ ] Generador de documentación BIM (plantas, cortes, fachadas)
- [ ] Soporte de subsuelos y cocheras
- [ ] Perfiles normativos adicionales

---

## 8) Métricas de Éxito y KPI

| KPI | Definición | Target |
|---|---|---|
| Velocidad de preview | Tiempo de regeneración ante cambio de parámetro | < 2 segundos |
| Cobertura de validación | % de reglas normativas implementadas vs definidas | ≥ 80% en Fase 2 |
| Tasa de exportación exitosa | % de modelos exportados sin errores críticos en Revit | ≥ 90% en Fase 3 |
| Eficiencia del layout | Ratio superficie vendible / superficie total de planta | Reportado; target > 75% |
| Tiempo de generación completa | Desde parámetros hasta modelo en Revit | < 5 minutos para edificio de 8 pisos |
| Cobertura de tipologías | Cantidad de tipologías de departamento soportadas | ≥ 3 en Fase 2; ≥ 6 en Fase 4 |

---

## 9) Recomendaciones de Diseño y Tecnología

### Arquitectura de módulos recomendada

```
bim_generator/
├── core/
│   ├── parameter_engine.py      # Motor de parámetros y jerarquía
│   ├── rule_engine.py           # Motor de reglas de diseño
│   └── validator.py             # Validador normativo (perfiles por país)
├── generators/
│   ├── architectural.py         # Generador de plantas, muros, ambientes
│   ├── structural.py            # Grilla estructural, columnas, vigas
│   ├── circulation.py           # Núcleos, pasillos, escaleras, ascensores
│   └── facade.py                # Generador de fachadas y balcones
├── preview/
│   ├── engine.py                # Motor de preview geométrica (independiente de Revit)
│   └── renderers/               # Un renderer por tipo de preview
├── revit/
│   ├── exporter.py              # Capa de abstracción de la API de Revit
│   └── element_factory.py       # Creación de elementos Revit
├── ui/
│   ├── main_window.py           # Ventana principal PyQt6
│   ├── panels/                  # Un panel por sección de configuración
│   └── preview_widget.py        # Widget de preview contextual
├── config/
│   ├── norms/
│   │   └── argentina.json       # Perfil normativo Argentina
│   └── typologies/
│       └── residential.yaml     # Tipologías de departamentos
└── reports/
    └── generator.py             # Generador de reportes PDF/Excel
```

### Decisiones técnicas clave

**Preview geométrica:** Evaluar en este orden por complejidad creciente:
1. `matplotlib` con Axes3D → inmediato, limitado en interactividad.
2. `VTK` via `pyvista` → excelente para geometría técnica, buena performance.
3. `PyOpenGL` → máxima flexibilidad, mayor costo de implementación.

**Recomendación inicial:** comenzar con `pyvista` (wrappea VTK con una API pythónica simple).

**Motor de parámetros:** Usar `Pydantic` para definir y validar los modelos de datos de parámetros. Permite validación automática, serialización a JSON y tipado estricto.

**Integración Revit:** La ruta de menor fricción inicial es `pyRevit` (scripts Python que corren dentro del entorno de Revit). Para automatización headless, explorar `revitpythonwrapper (RPW)`.

**Configuración normativa:** Cada perfil de país es un archivo JSON con la siguiente estructura mínima:
```json
{
  "profile": "argentina_caba",
  "fos_max": 0.6,
  "fot_max": 2.5,
  "min_room_areas": {
    "dormitorio_simple": 9.0,
    "dormitorio_principal": 12.0,
    "living_comedor": 16.0,
    "cocina": 6.0,
    "baño": 3.5
  },
  "max_evacuation_distance_m": 40,
  "min_natural_light_ratio": 0.125
}
```

---

## 10) Referencias a Buenas Prácticas y Justificativos

| Práctica | Fuente | Aplicación en este proyecto |
|---|---|---|
| Separación de concerns | Clean Architecture (R. Martin) | Módulos core, generators, ui, revit son capas independientes |
| Configuración externalizada | 12-Factor App | Toda normativa y tipología en archivos JSON/YAML |
| Validación con esquemas | ISO/IEC 25010 (calidad de software) | Pydantic para validar parámetros de entrada |
| Documentación como código | Docs-as-Code | Este Claude.md se versiona junto al código |
| Prototipado de UI antes de lógica | Lean UX | Fase 1 prioriza interfaz + preview antes de la integración Revit |
| Perfiles de configuración por contexto | PMBOK — gestión de adaptaciones | Perfiles normativos JSON por país/ciudad |
| Generación paramétrica modular | Principios de diseño generativo (Kolarevic) | Cada generador es intercambiable por otro con la misma interfaz |
| LOD progresivo en BIM | LOD Specification (BIMForum) | Preview usa LOD 100-200; exportación a Revit apunta a LOD 300 |

---

> **Nota para agentes de IA:** Al recibir este documento, asumir que el estado actual del proyecto corresponde a la última fase marcada con items completados (✅). Las secciones de "Backlog" no deben implementarse hasta que las fases anteriores estén cerradas. Ante dudas de alcance, consultar las exclusiones del §2 antes de proponer soluciones.
