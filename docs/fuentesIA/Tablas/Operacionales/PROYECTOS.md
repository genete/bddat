### PROYECTOS

Proyecto técnico único asociado a cada expediente.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del proyecto | NO | PK, autoincremental |
| **TITULO** | VARCHAR(500) | Título del proyecto técnico | NO | Descripción breve. Default: "⚠️ Falta el título del proyecto" |
| **DESCRIPCION** | VARCHAR(10000) | Descripción técnica del proyecto | NO | Texto libre extenso. Default: "⚠️ Falta la descripción del proyecto" |
| **FECHA** | DATE | Fecha de firma o visado del proyecto | NO | Fecha técnica del documento de proyecto (NO es fecha de presentación administrativa). Ayuda a identificar y ordenar versiones cronológicamente |
| **FINALIDAD** | VARCHAR(500) | Finalidad de la instalación | NO | Uso previsto. Default: "⚠️ Falta la finalidad del proyecto" |
| **EMPLAZAMIENTO** | VARCHAR(200) | Ubicación geográfica de la instalación | NO | Descripción textual. Default: "⚠️ Falta el emplazamiento" |
| **IA_ID** | INTEGER | Instrumento ambiental aplicable | SÍ | FK → TIPOS_IA(ID). Define figura ambiental (AAU, AAUS, CA, No sujeto) |

#### Claves

- **PK:** `ID`
- **FK:**
  - `IA_ID` → `TIPOS_IA(ID)`

#### Notas de Versión

- **v3.0:** **ELIMINADO** `EXPEDIENTE_ID`. Relación inversa (expediente apunta a proyecto).
- **v3.0:** **ELIMINADO** `TIPO_PROYECTO_ID`. Tipos de versión viven en `DOCUMENTOS_PROYECTO.TIPO`.
- **v3.0:** **ACLARADO** `FECHA`: Es fecha técnica del proyecto (firma/visado), NO fecha administrativa de presentación.

#### Filosofía

El proyecto es una **entidad técnica pura y única**. No tiene múltiples versiones en esta tabla. Las versiones documentales (proyecto inicial, modificados, refundidos) se gestionan mediante documentos vinculados en `DOCUMENTOS_PROYECTO`.

---