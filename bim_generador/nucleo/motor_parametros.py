"""
motor_parametros.py
-------------------
Motor de parámetros del BIM Generador.

Define la jerarquía completa de modelos Pydantic:
    Proyecto → Lote → Edificio → Planta → Unidad → Ambiente

Cada nivel tiene parámetros propios. Los cambios en niveles superiores
propagan restricciones hacia abajo a través de los métodos de validación.

Uso básico:
    from bim_generador.nucleo.motor_parametros import Proyecto, Lote, Edificio, Planta, Unidad, Ambiente
    proyecto = Proyecto.desde_predeterminados("Mi Edificio")
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, computed_field, model_validator


# ---------------------------------------------------------------------------
# Enumeraciones
# ---------------------------------------------------------------------------

class TipoAmbiente(str, Enum):
    """Tipos de ambiente según el código urbano de referencia."""
    DORMITORIO_SIMPLE    = "dormitorio_simple"
    DORMITORIO_PRINCIPAL = "dormitorio_principal"
    LIVING_COMEDOR       = "living_comedor"
    COCINA               = "cocina"
    BANIO                = "banio"
    TOILETTE             = "toilette"
    LAVADERO             = "lavadero"
    ESTUDIO              = "estudio"
    BALCON               = "balcon"
    CIRCULACION_INTERNA  = "circulacion_interna"


class TipoPlanta(str, Enum):
    """Tipo de planta según su posición en el edificio."""
    PLANTA_BAJA  = "planta_baja"
    PLANTA_TIPO  = "planta_tipo"
    ULTIMO_PISO  = "ultimo_piso"
    SUBSUELO     = "subsuelo"


class TipoUnidad(str, Enum):
    """Tipología de unidad funcional (departamento)."""
    MONOAMBIENTE = "monoambiente"
    DOS_AMBIENTES   = "2_ambientes"
    TRES_AMBIENTES  = "3_ambientes"
    CUATRO_AMBIENTES = "4_ambientes"
    DUPLEX          = "duplex"


class TipoEstructura(str, Enum):
    """Sistema estructural del edificio."""
    HORMIGON_ARMADO   = "hormigon_armado"
    METALICA          = "metalica"
    MIXTA             = "mixta"


# ---------------------------------------------------------------------------
# Nivel 6 — Ambiente
# ---------------------------------------------------------------------------

class Ambiente(BaseModel):
    """
    Unidad mínima de espacio dentro de una unidad funcional.

    Atributos:
        tipo            : Tipo de ambiente (dormitorio, cocina, etc.)
        superficie_m2   : Superficie en metros cuadrados
        ancho_min_m     : Ancho mínimo requerido en metros
        iluminacion_natural : Si tiene acceso a iluminación natural
        ventilacion_natural : Si tiene ventilación natural directa
        nombre_custom   : Nombre personalizado (opcional; si None se usa el tipo)
    """
    tipo: TipoAmbiente
    superficie_m2: float = Field(gt=0, description="Superficie en m²")
    ancho_min_m: float   = Field(gt=0, default=2.5, description="Ancho mínimo en m")
    iluminacion_natural: bool = True
    ventilacion_natural: bool = True
    nombre_custom: Optional[str] = None

    @property
    def nombre(self) -> str:
        """Nombre visible del ambiente."""
        return self.nombre_custom or self.tipo.value.replace("_", " ").title()

    @classmethod
    def predeterminados_por_tipo(cls, tipo: TipoAmbiente) -> "Ambiente":
        """
        Crea un Ambiente con valores por defecto razonables para cada tipo.
        Los valores mínimos se basan en el Código Urbano de CABA.
        """
        predeterminados: dict[TipoAmbiente, dict] = {
            TipoAmbiente.DORMITORIO_SIMPLE:    {"superficie_m2": 9.0,  "ancho_min_m": 2.5},
            TipoAmbiente.DORMITORIO_PRINCIPAL: {"superficie_m2": 12.0, "ancho_min_m": 3.0},
            TipoAmbiente.LIVING_COMEDOR:       {"superficie_m2": 18.0, "ancho_min_m": 3.5},
            TipoAmbiente.COCINA:               {"superficie_m2": 6.0,  "ancho_min_m": 2.0},
            TipoAmbiente.BANIO:                {"superficie_m2": 3.5,  "ancho_min_m": 1.5},
            TipoAmbiente.TOILETTE:             {"superficie_m2": 2.0,  "ancho_min_m": 1.2},
            TipoAmbiente.LAVADERO:             {"superficie_m2": 2.5,  "ancho_min_m": 1.5},
            TipoAmbiente.ESTUDIO:              {"superficie_m2": 8.0,  "ancho_min_m": 2.5},
            TipoAmbiente.BALCON:               {"superficie_m2": 5.0,  "ancho_min_m": 1.5,
                                                "iluminacion_natural": True, "ventilacion_natural": True},
            TipoAmbiente.CIRCULACION_INTERNA:  {"superficie_m2": 3.0,  "ancho_min_m": 0.9,
                                                "iluminacion_natural": False, "ventilacion_natural": False},
        }
        kw = {"tipo": tipo, **predeterminados.get(tipo, {"superficie_m2": 6.0, "ancho_min_m": 2.0})}
        return cls(**kw)

    # Alias para compatibilidad con código legado
    @classmethod
    def defaults_para_tipo(cls, tipo: TipoAmbiente) -> "Ambiente":
        return cls.predeterminados_por_tipo(tipo)


# ---------------------------------------------------------------------------
# Nivel 5 — Unidad funcional (departamento)
# ---------------------------------------------------------------------------

class Unidad(BaseModel):
    """
    Unidad funcional (departamento) dentro de una planta.

    Atributos:
        tipologia       : Categoría de la unidad (2 amb, 3 amb, etc.)
        ambientes       : Lista de ambientes que componen la unidad
        tiene_balcon    : Si la unidad incluye balcón
        orientacion     : Orientación principal (N, S, E, O, NE, etc.)
        codigo          : Identificador único dentro de la planta (ej: "A", "B", "01")
    """
    tipologia: TipoUnidad
    ambientes: list[Ambiente] = Field(default_factory=list)
    tiene_balcon: bool = False
    orientacion: str = "N"
    codigo: str = "A"

    @computed_field
    @property
    def superficie_total_m2(self) -> float:
        """Suma de superficies de todos los ambientes."""
        return round(sum(a.superficie_m2 for a in self.ambientes), 2)

    @computed_field
    @property
    def superficie_vendible_m2(self) -> float:
        """Superficie vendible: excluye circulación interna."""
        return round(sum(
            a.superficie_m2 for a in self.ambientes
            if a.tipo != TipoAmbiente.CIRCULACION_INTERNA
        ), 2)

    @computed_field
    @property
    def cantidad_dormitorios(self) -> int:
        return sum(
            1 for a in self.ambientes
            if a.tipo in (TipoAmbiente.DORMITORIO_SIMPLE, TipoAmbiente.DORMITORIO_PRINCIPAL)
        )

    @classmethod
    def desde_tipologia(cls, tipologia: TipoUnidad, codigo: str = "A") -> "Unidad":
        """
        Crea una unidad con la distribución de ambientes estándar
        para cada tipología.
        """
        composicion: dict[TipoUnidad, list[TipoAmbiente]] = {
            TipoUnidad.MONOAMBIENTE: [
                TipoAmbiente.LIVING_COMEDOR,
                TipoAmbiente.COCINA,
                TipoAmbiente.BANIO,
                TipoAmbiente.CIRCULACION_INTERNA,
            ],
            TipoUnidad.DOS_AMBIENTES: [
                TipoAmbiente.DORMITORIO_SIMPLE,
                TipoAmbiente.LIVING_COMEDOR,
                TipoAmbiente.COCINA,
                TipoAmbiente.BANIO,
                TipoAmbiente.CIRCULACION_INTERNA,
            ],
            TipoUnidad.TRES_AMBIENTES: [
                TipoAmbiente.DORMITORIO_PRINCIPAL,
                TipoAmbiente.DORMITORIO_SIMPLE,
                TipoAmbiente.LIVING_COMEDOR,
                TipoAmbiente.COCINA,
                TipoAmbiente.BANIO,
                TipoAmbiente.CIRCULACION_INTERNA,
            ],
            TipoUnidad.CUATRO_AMBIENTES: [
                TipoAmbiente.DORMITORIO_PRINCIPAL,
                TipoAmbiente.DORMITORIO_SIMPLE,
                TipoAmbiente.DORMITORIO_SIMPLE,
                TipoAmbiente.LIVING_COMEDOR,
                TipoAmbiente.COCINA,
                TipoAmbiente.BANIO,
                TipoAmbiente.TOILETTE,
                TipoAmbiente.CIRCULACION_INTERNA,
            ],
        }
        tipos = composicion.get(tipologia, composicion[TipoUnidad.DOS_AMBIENTES])
        ambientes = [Ambiente.predeterminados_por_tipo(t) for t in tipos]
        tiene_balcon = tipologia not in (TipoUnidad.MONOAMBIENTE,)
        return cls(tipologia=tipologia, ambientes=ambientes,
                   tiene_balcon=tiene_balcon, codigo=codigo)


# ---------------------------------------------------------------------------
# Nivel 4 — Planta
# ---------------------------------------------------------------------------

class NucleoVertical(BaseModel):
    """
    Núcleo de circulación vertical (escalera + ascensor).

    Atributos:
        ancho_m          : Ancho del núcleo en planta
        largo_m          : Largo del núcleo en planta
        tiene_ascensor   : Si incluye ascensor
        cantidad_escaleras: Número de escaleras
    """
    ancho_m: float = Field(default=4.0, gt=0)
    largo_m: float = Field(default=3.5, gt=0)
    tiene_ascensor: bool = True
    cantidad_escaleras: int = Field(default=1, ge=1)

    @computed_field
    @property
    def superficie_m2(self) -> float:
        return round(self.ancho_m * self.largo_m, 2)


class Planta(BaseModel):
    """
    Nivel (piso) del edificio.

    Atributos:
        numero          : Número de planta (0 = PB, 1 = 1er piso, etc.)
        tipo_planta     : Categoría de la planta
        altura_libre_m  : Altura libre entre losas en metros
        unidades        : Lista de unidades funcionales en esta planta
        nucleo          : Núcleo de circulación vertical
        ancho_pasillo_m : Ancho del pasillo de distribución
    """
    numero: int = Field(ge=0)
    tipo_planta: TipoPlanta = TipoPlanta.PLANTA_TIPO
    altura_libre_m: float = Field(default=2.65, gt=2.4)
    unidades: list[Unidad] = Field(default_factory=list)
    nucleo: NucleoVertical = Field(default_factory=NucleoVertical)
    ancho_pasillo_m: float = Field(default=1.4, ge=1.2)

    @computed_field
    @property
    def superficie_unidades_m2(self) -> float:
        return round(sum(u.superficie_total_m2 for u in self.unidades), 2)

    @computed_field
    @property
    def cantidad_unidades(self) -> int:
        return len(self.unidades)

    @computed_field
    @property
    def nombre(self) -> str:
        if self.tipo_planta == TipoPlanta.PLANTA_BAJA:
            return "Planta Baja"
        elif self.tipo_planta == TipoPlanta.ULTIMO_PISO:
            return f"{self.numero}° Piso (Último)"
        elif self.tipo_planta == TipoPlanta.SUBSUELO:
            return f"Subsuelo {abs(self.numero)}"
        else:
            return f"{self.numero}° Piso"


# ---------------------------------------------------------------------------
# Nivel 3 — Edificio
# ---------------------------------------------------------------------------

class ParametrosEstructurales(BaseModel):
    """
    Parámetros de la grilla estructural del edificio.

    Atributos:
        tipo_estructura     : Sistema estructural
        modulo_x_m          : Módulo estructural en dirección X (m)
        modulo_y_m          : Módulo estructural en dirección Y (m)
        seccion_columna_m   : Sección cuadrada de columnas (m)
        espesor_losa_m      : Espesor de losa en metros
        espesor_muro_ext_m  : Espesor de muros exteriores (m)
        espesor_muro_int_m  : Espesor de muros interiores (m)
    """
    tipo_estructura: TipoEstructura = TipoEstructura.HORMIGON_ARMADO
    modulo_x_m: float = Field(default=5.5, gt=3.0, le=9.0)
    modulo_y_m: float = Field(default=5.5, gt=3.0, le=9.0)
    seccion_columna_m: float = Field(default=0.30, gt=0.20, le=0.80)
    espesor_losa_m: float = Field(default=0.20, gt=0.12, le=0.40)
    espesor_muro_ext_m: float = Field(default=0.20, gt=0.10, le=0.40)
    espesor_muro_int_m: float = Field(default=0.15, gt=0.08, le=0.30)


class Edificio(BaseModel):
    """
    Edificio residencial completo.

    Atributos:
        nombre              : Nombre del proyecto/edificio
        cantidad_pisos      : Cantidad de pisos sobre nivel 0 (sin PB)
        incluye_pb          : Si incluye planta baja diferenciada
        plantas             : Lista de plantas del edificio
        estructura          : Parámetros estructurales
        retiro_frontal_m    : Retiro frontal obligatorio (m)
        retiro_lateral_m    : Retiro lateral obligatorio (m)
        retiro_posterior_m  : Retiro posterior obligatorio (m)
    """
    nombre: str = "Edificio"
    cantidad_pisos: int = Field(default=7, ge=1, le=50)
    incluye_pb: bool = True
    plantas: list[Planta] = Field(default_factory=list)
    estructura: ParametrosEstructurales = Field(default_factory=ParametrosEstructurales)
    retiro_frontal_m: float = Field(default=3.0, ge=0.0)
    retiro_lateral_m: float = Field(default=3.0, ge=0.0)
    retiro_posterior_m: float = Field(default=3.0, ge=0.0)

    @computed_field
    @property
    def total_plantas(self) -> int:
        return len(self.plantas)

    @computed_field
    @property
    def altura_total_m(self) -> float:
        """Altura total aproximada del edificio."""
        if not self.plantas:
            return 0.0
        return round(sum(p.altura_libre_m + self.estructura.espesor_losa_m
                         for p in self.plantas), 2)

    @computed_field
    @property
    def total_unidades(self) -> int:
        return sum(p.cantidad_unidades for p in self.plantas)

    @computed_field
    @property
    def superficie_total_unidades_m2(self) -> float:
        return round(sum(p.superficie_unidades_m2 for p in self.plantas), 2)

    def generar_plantas_tipo(self, unidades_por_planta: list[Unidad]) -> None:
        """
        Popula la lista de plantas con la distribución de unidades indicada.
        Genera: 1 PB + N plantas tipo + 1 último piso.
        """
        self.plantas = []
        total = self.cantidad_pisos + (1 if self.incluye_pb else 0)
        for i in range(total):
            if i == 0 and self.incluye_pb:
                tipo = TipoPlanta.PLANTA_BAJA
            elif i == total - 1:
                tipo = TipoPlanta.ULTIMO_PISO
            else:
                tipo = TipoPlanta.PLANTA_TIPO

            # Reasignar códigos de unidad para evitar duplicados
            unidades_copia = []
            for idx, u in enumerate(unidades_por_planta):
                u_copia = u.model_copy(update={"codigo": f"{chr(65+idx)}{i}"})
                unidades_copia.append(u_copia)

            planta = Planta(numero=i, tipo_planta=tipo, unidades=unidades_copia)
            self.plantas.append(planta)


# ---------------------------------------------------------------------------
# Nivel 2 — Lote
# ---------------------------------------------------------------------------

class Lote(BaseModel):
    """
    Lote urbanístico sobre el que se implanta el edificio.

    Atributos:
        frente_m            : Frente del lote en metros
        fondo_m             : Fondo del lote en metros
        forma               : Forma del lote ('rectangular', 'irregular')
        fos_max             : Factor de Ocupación del Suelo máximo permitido
        fot_max             : Factor de Ocupación Total máximo permitido
        altura_max_m        : Altura máxima permitida por normativa
        cota_terreno_m      : Cota de nivel de terreno respecto al cordón
    """
    frente_m: float = Field(default=15.0, gt=4.0)
    fondo_m: float  = Field(default=30.0, gt=8.0)
    forma: str      = Field(default="rectangular")
    fos_max: float  = Field(default=0.60, gt=0.0, le=1.0)
    fot_max: float  = Field(default=2.5,  gt=0.0, le=10.0)
    altura_max_m: Optional[float] = Field(default=None, gt=0.0)
    cota_terreno_m: float = Field(default=0.0)

    @computed_field
    @property
    def superficie_m2(self) -> float:
        return round(self.frente_m * self.fondo_m, 2)

    @computed_field
    @property
    def superficie_edificable_m2(self) -> float:
        """Superficie máxima de huella de planta baja (FOS)."""
        return round(self.superficie_m2 * self.fos_max, 2)

    @computed_field
    @property
    def superficie_total_construible_m2(self) -> float:
        """Superficie máxima total construible (FOT)."""
        return round(self.superficie_m2 * self.fot_max, 2)


# ---------------------------------------------------------------------------
# Nivel 1 — Proyecto
# ---------------------------------------------------------------------------

class MetadatosProyecto(BaseModel):
    """Metadatos administrativos del proyecto."""
    cliente: str = ""
    arquitecto: str = ""
    ubicacion: str = ""
    ciudad: str = "Buenos Aires"
    pais: str = "Argentina"
    perfil_normativo: str = "argentina_caba"
    descripcion: str = ""


class Proyecto(BaseModel):
    """
    Proyecto de edificio residencial. Nivel raíz de la jerarquía de parámetros.

    Contiene la configuración completa: metadatos, lote y edificio.

    Ejemplo de uso:
        proyecto = Proyecto.desde_predeterminados("Torre Palermo")
        proyecto.lote.frente_m = 20.0
        proyecto.edificio.cantidad_pisos = 10
    """
    nombre: str
    metadatos: MetadatosProyecto = Field(default_factory=MetadatosProyecto)
    lote: Lote = Field(default_factory=Lote)
    edificio: Edificio = Field(default_factory=Edificio)

    @model_validator(mode="after")
    def sincronizar_nombre_edificio(self) -> "Proyecto":
        """Mantiene el nombre del edificio sincronizado con el del proyecto."""
        if self.edificio.nombre == "Edificio":
            self.edificio.nombre = self.nombre
        return self

    @classmethod
    def desde_predeterminados(cls, nombre: str = "Nuevo Proyecto") -> "Proyecto":
        """
        Crea un proyecto con configuración por defecto lista para editar.
        Genera un edificio de 7 pisos con una distribución simple de
        2 unidades de 2 ambientes y 1 unidad de 3 ambientes por planta.
        """
        proyecto = cls(nombre=nombre)

        # Distribución estándar por planta tipo
        unidades_tipo = [
            Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES,   codigo="A"),
            Unidad.desde_tipologia(TipoUnidad.DOS_AMBIENTES,   codigo="B"),
            Unidad.desde_tipologia(TipoUnidad.TRES_AMBIENTES,  codigo="C"),
        ]
        proyecto.edificio.generar_plantas_tipo(unidades_tipo)
        return proyecto

    # Alias para compatibilidad con código legado
    @classmethod
    def desde_defaults(cls, nombre: str = "Nuevo Proyecto") -> "Proyecto":
        return cls.desde_predeterminados(nombre)

    # ---- helpers de métricas -----------------------------------------------

    def calcular_fos_real(self) -> float:
        """FOS real: huella PB / superficie de lote."""
        if not self.edificio.plantas:
            return 0.0
        planta_baja = next((p for p in self.edificio.plantas
                            if p.tipo_planta == TipoPlanta.PLANTA_BAJA), None)
        if planta_baja is None:
            return 0.0
        huella = planta_baja.superficie_unidades_m2 + planta_baja.nucleo.superficie_m2
        return round(huella / self.lote.superficie_m2, 3)

    def calcular_fot_real(self) -> float:
        """FOT real: superficie total construida / superficie de lote."""
        if self.lote.superficie_m2 == 0:
            return 0.0
        return round(self.edificio.superficie_total_unidades_m2 / self.lote.superficie_m2, 3)

    def resumen(self) -> dict:
        """Resumen ejecutivo del proyecto con métricas clave."""
        return {
            "nombre": self.nombre,
            "ubicacion": self.metadatos.ubicacion,
            "lote_m2": self.lote.superficie_m2,
            "cantidad_pisos": self.edificio.cantidad_pisos,
            "altura_total_m": self.edificio.altura_total_m,
            "total_unidades": self.edificio.total_unidades,
            "superficie_total_construida_m2": self.edificio.superficie_total_unidades_m2,
            "fos_real": self.calcular_fos_real(),
            "fot_real": self.calcular_fot_real(),
            "fos_max_permitido": self.lote.fos_max,
            "fot_max_permitido": self.lote.fot_max,
        }

    def a_json(self, indent: int = 2) -> str:
        """Serializa el proyecto completo a JSON."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def desde_json(cls, json_str: str) -> "Proyecto":
        """Deserializa un proyecto desde JSON."""
        return cls.model_validate_json(json_str)
