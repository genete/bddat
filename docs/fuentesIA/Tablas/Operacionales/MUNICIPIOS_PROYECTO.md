### MUNICIPIOS_PROYECTO

Relación muchos a muchos entre proyectos y municipios afectados.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **MUNICIPIO_ID** | INTEGER | Municipio afectado por el proyecto | NO | FK → MUNICIPIOS(ID). Municipio por donde discurre la instalación o donde se ubica |
| **PROYECTO_ID** | INTEGER | Proyecto que afecta al municipio | NO | FK → PROYECTOS(ID). Proyecto técnico del expediente |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(MUNICIPIO_ID, PROYECTO_ID)` - Un municipio no puede vincularse dos veces al mismo proyecto
- **FK:**
  - `MUNICIPIO_ID` → `MUNICIPIOS(ID)`
  - `PROYECTO_ID` → `PROYECTOS(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `PROYECTO_ID` (municipios de un proyecto)
- `MUNICIPIO_ID` (proyectos que afectan a un municipio)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. Continúa siendo relación N:M entre proyectos y municipios.

#### Filosofía

Tabla intermedia que gestiona la relación **muchos a muchos** entre proyectos y municipios:

- Un proyecto puede afectar múltiples municipios (línea que atraviesa varios términos)
- Un municipio puede tener múltiples proyectos que lo afectan
- Necesaria para determinar publicaciones en tablones, consultas a ayuntamientos y análisis territorial

#### Uso Administrativo

**Derivaciones:**

- Determinar qué ayuntamientos deben ser consultados
- Publicaciones en tablones municipales (fase INFORMACION_PUBLICA)
- Generación de separatas por término municipal
- Evaluación ambiental diferente según afecte a más de un municipio

**Consultas típicas:**

**Municipios de un expediente:**
```
EXPEDIENTES → PROYECTO_ID → MUNICIPIOS_PROYECTO → MUNICIPIOS
```

**Expedientes que afectan a un municipio:**
```
MUNICIPIOS → MUNICIPIOS_PROYECTO → PROYECTOS → EXPEDIENTES
```

---