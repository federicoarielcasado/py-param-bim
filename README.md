# BIM Parametric Building Generator 🏗️

**Herramienta de escritorio para generar modelos BIM de edificios residenciales a partir de parámetros configurables**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-41CD52?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![Tests](https://img.shields.io/badge/Tests-40%2F40%20pasando-brightgreen?logo=pytest)](pruebas/)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-blue)](LICENSE)
[![Estado](https://img.shields.io/badge/Estado-Fase%201%20en%20desarrollo-orange)](README.md)

---

## 📋 Descripción

Sistema de generación paramétrica de edificios residenciales para Autodesk Revit. A partir de parámetros definidos por el usuario (lote, volumen, tipologías de departamentos, estructura), genera automáticamente la geometría del edificio con preview 3D en tiempo real y exporta el modelo final a Revit.

| Módulo | Tecnología | Estado |
|---|---|---|
| Motor de parámetros | Pydantic v2 | ✅ Fase 1 |
| Interfaz gráfica | PyQt6 | ✅ Fase 1 |
| Preview 3D | pyvista / VTK | ✅ Fase 1 |
| Generación arquitectónica | Python puro | 🔲 Fase 2 |
| Validación normativa | JSON configurable | ✅ Parcial |
| Exportación a Revit | pyRevit / RPW | 🔲 Fase 3 |

### ✨ Características Principales

**Motor de parámetros**
- ✅ Jerarquía de parámetros: `Proyecto → Lote → Edificio → Planta → Unidad → Ambiente`
- ✅ Validación automática con Pydantic v2 (tipos, rangos, restricciones)
- ✅ Campos computados: superficie total, altura, FOS/FOT real, cantidad de unidades
- ✅ Tipologías de departamentos predefinidas: monoambiente, 2, 3 y 4 ambientes
- ✅ Serialización/deserialización JSON para guardar y cargar proyectos

**Interfaz gráfica**
- ✅ Ventana de tres columnas: navegación + configuración + preview 3D
- ✅ Preview contextual: cambia automáticamente según la sección activa
- ✅ Debounce en la actualización del preview (sin lag al tipear)
- ✅ Guardar y abrir proyectos en formato JSON
- ✅ Métricas del proyecto calculadas en tiempo real

**Validación normativa**
- ✅ Perfil Argentina — Código Urbano CABA: FOS, FOT, superficies mínimas
- ✅ Arquitectura de perfiles: extensible a otras ciudades/países vía JSON
- 🔲 Validación de iluminación y ventilación (Fase 2)
- 🔲 Distancias de evacuación (Fase 2)

**Exportación BIM**
- 🔲 Muros, losas, columnas, vigas a Revit (Fase 3)
- 🔲 Reportes de superficie en PDF/Excel (Fase 3)

---

## 🚀 Instalación

**Requisitos previos**
- Windows 10/11
- Python 3.10 o superior
- Autodesk Revit 2022+ con licencia activa *(solo para exportación — Fase 3)*

**Pasos**

```bash
# 1. Clonar el repositorio
git clone https://github.com/federicoarielcasado/py-param-bim.git
cd py-param-bim

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar pyvistaqt (widget 3D para PyQt6)
pip install pyvistaqt

# 4. Verificar instalación
python -m pytest pruebas/ -v

# 5. Lanzar la aplicación
python main.py
```

### Dependencias Principales

| Librería | Versión mínima | Para qué sirve |
|---|---|---|
| `pydantic` | 2.0.0 | Motor de parámetros y validación de modelos |
| `PyQt6` | 6.6.0 | Interfaz gráfica de escritorio (Windows) |
| `pyvista` | 0.43.0 | Visualización 3D paramétrica (wrappea VTK) |
| `vtk` | 9.2.0 | Backend de renderizado geométrico |
| `pyvistaqt` | 0.11.0 | Widget Qt para embeber pyvista en PyQt6 |
| `PyYAML` | 6.0 | Lectura de tipologías de departamentos |
| `pytest` | 7.0.0 | Framework de pruebas automatizadas |

---

## 📖 Guía de Uso

### Caso 1 — Lanzar la interfaz gráfica

```bash
python main.py
```

La ventana abre con un proyecto por defecto (lote 15×30 m, edificio de 7 pisos, 3 unidades por planta). El preview 3D del volumen aparece inmediatamente.

### Caso 2 — Crear y modificar un proyecto desde código

```python
from bim_generador.nucleo.motor_parametros import (
    Proyecto, TipoUnidad, Unidad
)

# Crear proyecto con valores predeterminados
proyecto = Proyecto.desde_predeterminados("Torre Palermo")

# Modificar parámetros del lote
proyecto.lote.frente_m = 20.0
proyecto.lote.fondo_m  = 40.0
proyecto.lote.fos_max  = 0.60
proyecto.lote.fot_max  = 3.0

# Modificar el edificio
proyecto.edificio.cantidad_pisos = 10
proyecto.edificio.retiro_frontal_m = 4.0

# Definir distribución de unidades por planta
unidades = [
    Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES,    codigo="A"),
    Unidad.desde_tipologia(TipoUnidad.TRES_AMBIENTES,   codigo="B"),
    Unidad.desde_tipologia(TipoUnidad.CUATRO_AMBIENTES, codigo="C"),
]
proyecto.edificio.generar_plantas_tipo(unidades)

# Ver métricas calculadas
print(proyecto.resumen())
# {
#   "nombre": "Torre Palermo",
#   "lote_m2": 800.0,
#   "cantidad_pisos": 10,
#   "altura_total_m": 29.7,
#   "total_unidades": 33,
#   "superficie_total_construida_m2": 4158.0,
#   "fos_real": 0.198,
#   "fot_real": 5.197,
#   ...
# }
```

### Caso 3 — Guardar y cargar proyectos

```python
# Guardar a JSON
json_str = proyecto.a_json()
with open("torre_palermo.json", "w", encoding="utf-8") as f:
    f.write(json_str)

# Cargar desde JSON
from bim_generador.nucleo.motor_parametros import Proyecto

with open("torre_palermo.json", encoding="utf-8") as f:
    proyecto = Proyecto.desde_json(f.read())

print(proyecto.nombre)  # "Torre Palermo"
print(proyecto.edificio.total_unidades)  # 33
```

### Caso 4 — Validar contra normativa

```python
from bim_generador.nucleo.validador import Validador

# Cargar perfil Argentina — CABA
validador = Validador("argentina_caba")
resultados = validador.validar(proyecto)

# Filtrar incumplimientos
incumplimientos = [r for r in resultados if not r.cumple]
for r in incumplimientos:
    print(r)
# ❌ [FOT] FOT real 5.20 > máximo 2.50
# ❌ [sup_min.cocina] [1° Piso / Unidad A0] Cocina: 5.5 m² < mínimo 6.0 m²
```

### Caso 5 — Consultar tipologías de ambientes

```python
from bim_generador.nucleo.motor_parametros import Ambiente, TipoAmbiente

# Crear ambiente con valores predeterminados del Código Urbano CABA
dormitorio = Ambiente.predeterminados_por_tipo(TipoAmbiente.DORMITORIO_PRINCIPAL)
print(dormitorio.superficie_m2)  # 12.0
print(dormitorio.ancho_min_m)    # 3.0
print(dormitorio.iluminacion_natural)  # True
```

---

## 📐 Fundamento Teórico

### Jerarquía de parámetros

El sistema modela un edificio residencial como una jerarquía de objetos anidados. Los parámetros de niveles superiores propagan restricciones hacia abajo:

```
Proyecto
└── Lote          → superficie, FOS/FOT, restricciones normativas
    └── Edificio  → pisos, retiros, grilla estructural
        └── Planta → tipo (PB/tipo/último), altura libre, núcleo vertical
            └── Unidad → tipología, orientación, balance de superficies
                └── Ambiente → tipo, superficie, iluminación, ventilación
```

### Factores urbanísticos (CABA)

```
FOS (Factor de Ocupación del Suelo) = Huella PB / Superficie de lote
FOT (Factor de Ocupación Total)     = Superficie construida total / Superficie de lote

Restricciones zona R2b (referencia):
  FOS ≤ 0.60
  FOT ≤ 2.50
```

### LOD (Level of Development) según BIMForum

| Fase | LOD | Contenido |
|---|---|---|
| Preview 3D (Fase 1) | LOD 100 | Volumen conceptual — bounding box por planta |
| Generación arquitectónica (Fase 2) | LOD 200 | Muros, losas, aberturas aproximadas |
| Exportación Revit (Fase 3) | LOD 300 | Geometría definida, parámetros de fabricación |

---

## 🧩 Arquitectura del Software

```
py-param-bim/
├── main.py                              # Punto de entrada
├── requirements.txt                     # Dependencias Python
├── pytest.ini                           # Configuración de pruebas en español
├── bim_generador/
│   ├── nucleo/
│   │   ├── motor_parametros.py          # Modelos Pydantic (jerarquía completa)
│   │   ├── motor_reglas.py              # Reglas de diseño entre niveles [Fase 2]
│   │   └── validador.py                 # Validador normativo por perfil de país
│   ├── generadores/
│   │   ├── arquitectonico.py            # Muros, losas, aberturas [Fase 2]
│   │   ├── estructural.py               # Grilla columnas/vigas [Fase 2]
│   │   ├── circulacion.py               # Núcleos y pasillos [Fase 2]
│   │   └── fachada.py                   # Fachadas y balcones [Fase 2]
│   ├── vista_previa/
│   │   ├── motor.py                     # Coordinador de renderizadores
│   │   └── renderizadores/
│   │       ├── volumen.py               # Preview volumétrico 3D ✅
│   │       ├── lote.py                  # Vista superior de implantación [Fase 2]
│   │       ├── unidad.py                # Planta de departamento [Fase 2]
│   │       └── estructura.py            # Grilla estructural [Fase 2]
│   ├── interfaz/
│   │   ├── ventana_principal.py         # Ventana 3 columnas (PyQt6)
│   │   ├── widget_vista.py              # Widget pyvista embebido
│   │   └── paneles/                     # Un panel por sección de configuración
│   ├── revit/
│   │   ├── exportador.py                # Capa de abstracción API Revit [Fase 3]
│   │   └── fabrica_elementos.py         # Creación de elementos Revit [Fase 3]
│   ├── configuracion/
│   │   ├── normas/argentina_caba.json   # Perfil normativo Argentina — CABA
│   │   └── tipologias/residential.yaml  # Biblioteca de tipologías
│   └── reportes/
│       └── generador.py                 # PDF/Excel [Fase 3]
└── pruebas/
    ├── prueba_motor_parametros.py        # 34 pruebas del motor
    └── prueba_validador.py               # 6 pruebas del validador
```

**Flujo de datos principal:**

```
┌──────────────┐    parametros_cambiados    ┌──────────────┐
│   PanelXxx   │ ─────────────────────────► │VentanaPrinc. │
└──────────────┘                            └──────┬───────┘
                                                   │ debounce (400ms)
                                                   ▼
                                           ┌──────────────┐
                                           │  MotorVista  │
                                           └──────┬───────┘
                                                   │ SeccionActiva
                                                   ▼
                                    ┌──────────────────────────┐
                                    │  RenderizadorVolumen     │
                                    │  (u otro según sección)  │
                                    └──────────┬───────────────┘
                                               │ pv.MultiBlock
                                               ▼
                                        ┌─────────────┐
                                        │ WidgetVista │ ◄── pyvista/VTK
                                        └─────────────┘
```

---

## 🧪 Testing

```bash
# Correr todas las pruebas
python -m pytest pruebas/ -v

# Solo motor de parámetros
python -m pytest pruebas/prueba_motor_parametros.py -v

# Solo validador
python -m pytest pruebas/prueba_validador.py -v

# Con reporte de cobertura
python -m pytest pruebas/ --cov=bim_generador --cov-report=term-missing
```

| Módulo de prueba | Clases cubiertas | Pruebas | Estado |
|---|---|---|---|
| `prueba_motor_parametros.py` | `Ambiente`, `Unidad`, `Planta`, `Lote`, `Edificio`, `Proyecto` | 34 | ✅ 34/34 |
| `prueba_validador.py` | `Validador`, `ResultadoValidacion` | 6 | ✅ 6/6 |
| **Total** | | **40** | **✅ 40/40** |

Casos de validación cubiertos:

| Caso | Descripción | Resultado esperado |
|---|---|---|
| Superficie de ambiente negativa | `Ambiente(superficie_m2=-5)` | `ValidationError` |
| Altura libre < 2.40 m | `Planta(altura_libre_m=2.0)` | `ValidationError` |
| FOS máx > 1.0 | `Lote(fos_max=1.5)` | `ValidationError` |
| Roundtrip JSON | `desde_json(proyecto.a_json())` | Proyecto idéntico |
| Sincronización nombre | `Proyecto(nombre="X")` | `edificio.nombre == "X"` |
| Perfil normativo inexistente | `Validador("pais_x")` | `FileNotFoundError` |

---

## 📚 API Principal

### `Proyecto`

```python
class Proyecto(BaseModel):
    nombre:    str
    metadatos: MetadatosProyecto
    lote:      Lote
    edificio:  Edificio
```

| Método | Parámetros | Retorna | Descripción |
|---|---|---|---|
| `desde_predeterminados(nombre)` | `nombre: str` | `Proyecto` | Crea proyecto con lote 15×30m, 7 pisos, 3 unidades/planta |
| `resumen()` | — | `dict` | Métricas clave: superficie, pisos, FOT/FOS real, unidades |
| `calcular_fos_real()` | — | `float` | FOS = huella PB / superficie lote |
| `calcular_fot_real()` | — | `float` | FOT = superficie construida total / superficie lote |
| `a_json(indent)` | `indent: int = 2` | `str` | Serializa proyecto completo a JSON |
| `desde_json(json_str)` | `json_str: str` | `Proyecto` | Deserializa desde JSON |

### `Unidad`

```python
class Unidad(BaseModel):
    tipologia:   TipoUnidad
    ambientes:   list[Ambiente]
    tiene_balcon: bool
    orientacion: str
    codigo:      str
```

| Campo computado | Tipo | Descripción |
|---|---|---|
| `superficie_total_m2` | `float` | Suma de superficies de todos los ambientes |
| `superficie_vendible_m2` | `float` | Excluye circulación interna |
| `cantidad_dormitorios` | `int` | Conteo de dormitorios simples y principales |

### `Validador`

```python
class Validador:
    def __init__(self, perfil: str = "argentina_caba"): ...
    def validar(self, proyecto: Proyecto) -> list[ResultadoValidacion]: ...
```

| Regla validada | Criterio | Norma |
|---|---|---|
| `FOS` | Huella PB ≤ FOS máx × superficie lote | Código Urbano CABA |
| `FOT` | Superficie construida ≤ FOT máx × superficie lote | Código Urbano CABA |
| `sup_min.*` | Cada ambiente ≥ superficie mínima por tipo | Código Urbano CABA Art. 4.3 |

---

## 🎓 Referencias

1. Municipalidad de Buenos Aires (2018). *Código Urbano — Ciudad Autónoma de Buenos Aires*. GCBA.
2. CIRSOC (2005). *Reglamento Argentino de Estructuras de Hormigón CIRSOC 201-2005*. INTI.
3. BIMForum (2023). *Level of Development (LOD) Specification*. BIMForum.
4. Martin, R. C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.
5. Kolarevic, B. (2003). *Architecture in the Digital Age: Design and Manufacturing*. Spon Press.

---

## 📝 Changelog

### v0.1.0 (13 de Marzo de 2026)

- ✅ Scaffolding completo del proyecto con nomenclatura en español
- ✅ Motor de parámetros: jerarquía completa `Proyecto → Ambiente` con Pydantic v2
- ✅ Validador normativo con perfil `argentina_caba` (FOS, FOT, superficies mínimas)
- ✅ Interfaz gráfica (PyQt6): ventana principal de 3 columnas funcional
- ✅ Panel general: edición de lote y edificio con métricas en tiempo real
- ✅ Renderizador volumétrico 3D (pyvista): preview del edificio sobre el lote
- ✅ Configuración externa: `argentina_caba.json` y `residential.yaml`
- ✅ 40 pruebas automatizadas (40/40 pasando)
- ✅ Repositorio en GitHub con `.gitignore` y `.gitattributes`
- [ ] Generadores arquitectónicos (muros, losas, aberturas) — Fase 2
- [ ] Panel de Lote / Implantación — Fase 2
- [ ] Panel de Tipologías de departamentos — Fase 2
- [ ] Validación de iluminación y ventilación — Fase 2
- [ ] Exportación a Revit — Fase 3

---

## 📄 Licencia

Distribuido bajo la [Licencia MIT](LICENSE).

---

## 👨‍💻 Autor

**Federico Casado**
Ingeniero Civil — Especialización en Python, finanzas e ingeniería estructural
Stack: Python · PyQt6 · pyvista/VTK · Pydantic · pyRevit
Dominio: Automatización BIM · Diseño paramétrico · Generación procedural

---

*Última actualización: 13 de Marzo de 2026*
