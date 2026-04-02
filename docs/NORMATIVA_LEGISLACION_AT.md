# NORMATIVA — Legislación aplicable al motor de reglas BDDAT

> **Fuente:** Legislación estatal y autonómica sobre instalaciones de alta tensión en Andalucía.
> **Aplica a:** Motor de reglas — base legal de las reglas de tramitación ESFTT.
> **Estado:** Catálogo de normas y estructura de extracción definida. Iteraciones de investigación pendientes.

---

## 1. Contexto del sistema BDDAT

La tramitación de cada expediente sigue la jerarquía ESFTT:

```
EXPEDIENTE (proyecto de instalación eléctrica)
  └── SOLICITUD (qué se pide: AAP, AAC, APO, utilidad pública...)
        └── FASE (etapas procedimentales: análisis, info pública, consultas, resolución...)
              └── TRÁMITE (acciones concretas dentro de la fase)
                    └── TAREA (unidad de trabajo: redactar, firmar, notificar, publicar, esperar plazo)
```

**Tipos de instalaciones de alta tensión:**
- Líneas eléctricas aéreas y subterráneas
- Subestaciones y centros de transformación
- Instalaciones de generación (renovable y convencional)
- Elementos de conexión y seccionamiento

**Tipos de solicitud:** AAP, AAC, APO, DUP, Modificación, Desistimiento/Renuncia
(Ver `docs/NORMATIVA_SOLICITUDES.md` para detalle y combinaciones.)

---

## 2. Legislación base

### Nacional
- **RD 1955/2000**, de 1 de diciembre — Regula actividades de transporte, distribución,
  comercialización, suministro y procedimientos de autorización de instalaciones de energía
  eléctrica. **Norma procedimental principal.**
- **Ley 24/2013**, de 26 de diciembre — Ley del Sector Eléctrico. Marco legal de referencia.
- **Ley 39/2015**, de 1 de octubre — Procedimiento Administrativo Común. Plazos,
  notificaciones, silencio administrativo. → Ver `docs/NORMATIVA_PLAZOS.md` para detalle de arts. 21-25, 29-32 y 112-126.
- **Ley 40/2015** — Régimen Jurídico del Sector Público (procedimiento interadministrativo).
- **RD 842/2002** — Reglamento Electrotécnico de Baja Tensión (referencia técnica complementaria).
- **Ley 21/2013** — Evaluación de Impacto Ambiental (EIA). Afecta a fases de consultas y
  pronunciamiento ambiental.

### Autonómica Andalucía
- **Decreto 9/2011**, de 18 de enero (BOJA nº 22) — Medidas para la agilización de trámites
  administrativos. Contiene excepciones relevantes al procedimiento estándar.
- **Ley 2/2007**, de 27 de marzo — Fomento de las Energías Renovables y del Ahorro y Eficiencia
  Energética de Andalucía.
- **Decreto 369/2010** y normas de desarrollo autonómico aplicables.
- **Decreto-ley 26/2021**, de 14 de diciembre — Simplificación administrativa. Incluye la
  Disposición Final Cuarta sobre exención de información pública para instalaciones sin DUP
  y sin AAU (ver DISEÑO_MOTOR_REGLAS.md, regla INICIAR INFORMACION_PUBLICA).

---

## 3. Qué extraer por tipo de solicitud

Para cada tipo de solicitud (AAP, AAC, APO, DUP...):
- Fases obligatorias y su orden
- Fases opcionales o condicionales
- Plazos legales aplicables (días hábiles o naturales)
- Puntos de silencio administrativo positivo/negativo
- Organismos de consulta obligatoria

### Variables que modifican las reglas estándar
- Tensión de la instalación (< 30 kV, 30-132 kV, > 132 kV)
- Tipo de instalación (aérea, subterránea, mixta)
- Clasificación del suelo afectado
- Longitud o potencia (umbrales de cambio de procedimiento)
- Tipo de promotor (distribuidora, generador, consumidor directo)
- Necesidad de EIA: cuándo es obligatoria
- Afectación a espacios protegidos (Red Natura 2000, ZEPA, LIC)
- Instalaciones de generación renovable (régimen especial)

### Excepciones y regímenes especiales
- Instalaciones exentas de alguna fase (DA1ª del Decreto 9/2011)
- Procedimientos abreviados o simplificados
- Régimen especial para generación renovable
- Instalaciones de uso privado vs. uso público
- Pequeñas instalaciones bajo umbrales de simplificación

---

## 4. Formato de documentación de reglas

Para cada regla identificada, documentar:

| Campo | Contenido |
|-------|-----------|
| ID_regla | Identificador único (ej: R-AAP-01) |
| Descripción | Qué dice la regla en lenguaje natural |
| Tipo_solicitud | A qué tipo de solicitud aplica |
| Fase_afectada | Qué fase(s) afecta |
| Condición_activación | Cuándo aplica (siempre / si tensión > X / si suelo urbano...) |
| Excepción_de | Si es excepción, a qué regla estándar contradice |
| Fuente_legal | Norma, artículo y apartado |
| Notas | Observaciones de interpretación |

---

## 5. Resultados por iteración

*(Se completarán en sesiones de trabajo dedicadas — ver issue #250 para planificación)*

### Iteración 1 — Mapa de alto nivel
Para cada tipo de solicitud estándar (AAP, AAC, APO, DUP):
qué fases son obligatorias según RD 1955/2000 y cuáles son los plazos.

### Iteración 2 — Excepciones y regímenes especiales
Generación renovable, instalaciones < 30 kV.

### Iteración 3 — Plazos y silencio administrativo
→ En curso. Ver `docs/NORMATIVA_PLAZOS.md` para extracción detallada por norma.
- §1 LPACAP 39/2015 — completo (sesión 2026-04-01)
- §2.1 LSE 24/2013 — completo (sesión 2026-04-02)
- §2.2 RD 1955/2000 — completo (sesión 2026-04-02)

### Iteración 4 — Casos límite y casuística especial

---

## 6. Fuentes normativas por ámbito — Junta de Andalucía

Páginas de referencia de la Consejería de Industria, Energía y Minas:

| Ámbito | URL |
|---|---|
| Energía eléctrica (distribución y transporte) | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/electricidad.html |
| Energías renovables | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/renovables.html |

---

### 6.1 Energía eléctrica — distribución y transporte

#### Normativa directa (introducción apartado 1)

Normas que la Consejería lista explícitamente como marco de las autorizaciones:

| Norma | URL | Observaciones |
|---|---|---|
| Ley 24/2013, de 26 de diciembre (LSE) | https://www.boe.es/eli/es/l/2013/12/26/24/con | → Ver NORMATIVA_PLAZOS §2.1 |
| RD 1955/2000, de 1 de diciembre | https://www.boe.es/eli/es/rd/2000/12/01/1955/con | → Ver NORMATIVA_PLAZOS §2.2 |
| RD 337/2014, de 9 de mayo (RAT) | https://www.boe.es/eli/es/rd/2014/05/09/337/con | Reglamento sobre condiciones técnicas y garantías de seguridad en instalaciones eléctricas de alta tensión. Referencia técnica; puede incidir en documentación de solicitudes. |
| RD 223/2008, de 15 de febrero | https://www.boe.es/eli/es/rd/2008/02/15/223/con | Reglamento sobre condiciones técnicas y garantías de seguridad en líneas eléctricas de alta tensión. |
| Instrucción 1/2023, de 11 de julio — SGE AT (pdf) | https://www.juntadeandalucia.es/sites/default/files/2023-10/7_20230711_INSTRUCCI%C3%93N%201-2023%20de%20SGE%20AT(F).pdf | Instrucción interna de la Secretaría General de Energía sobre tramitación AT. Pendiente de revisar. |
| Instrucción Conjunta 1/2022 — SGE + DGSAyCC (pdf) | https://www.juntadeandalucia.es/sites/default/files/inline-files/2022/10/INSTRUCCION_CONJUNTA_1_2022_SGE_DGSAyCC_F_F.pdf | Conjunta con la Dirección General de Sostenibilidad Ambiental y Cambio Climático. Relevante para trámites EIA. Pendiente de revisar. |
| Resolución de 13 de octubre de 2023 (BOJA 2023/206/75) | https://www.juntadeandalucia.es/boja/2023/206/75.html | Pendiente de identificar objeto. |

#### Procedimientos del catálogo

Los procedimientos oficiales del catálogo de la Consejería — cada ficha contiene normativa aplicable, plazo de resolución, documentación y efectos del silencio:

| Tipo | URL catálogo |
|---|---|
| Autorización administrativa previa (AAP) — producción, distribución, transporte y líneas directas | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/9588.html |
| Autorización administrativa de construcción (AAC) — producción, distribución, transporte y líneas directas | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11944.html |
| Autorización de explotación — instalaciones de producción (excl. líneas de evacuación) | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11954.html |
| Autorización de explotación — distribución, transporte secundario, acometidas (<380 kV), líneas directas e infraestructuras de evacuación | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11996.html |
| Autorización de transmisión — producción, distribución, transporte, líneas directas y líneas a ceder a transportista/distribuidora | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11955.html |
| Autorización de cierre — producción, distribución, transporte y líneas directas | https://www.juntadeandalucia.es/organismos/industriaenergiayminas/servicios/procedimientos/detalle/11963.html |

> Formulario electrónico de solicitud (VEA): https://ws050.juntadeandalucia.es/vea/accesoDirecto?codProcedimiento=CHFE_DGE_9588

#### Certificados eléctricos de alta tensión

Normativa de referencia para los certificados que acompañan la solicitud de AE:

| Norma | URL |
|---|---|
| RD 337/2014, de 9 de mayo (RAT) | https://www.boe.es/eli/es/rd/2014/05/09/337/con |
| RD 223/2008, de 15 de febrero | https://www.boe.es/eli/es/rd/2008/02/15/223/con |

#### Certificados eléctricos de baja tensión

*(Fuera del ámbito principal de BDDAT — anotado como referencia)*

| Norma / Recurso | URL |
|---|---|
| RD 842/2002, de 2 de agosto (REBT) | https://www.boe.es/buscar/act.php?id=BOE-A-2002-18099 |
| Decreto 59/2005 (BOJA 2005/118) | https://www.juntadeandalucia.es/boja/2005/118/3 |
| Orden de 5 de marzo de 2013 (BOJA 2013/48) | https://www.juntadeandalucia.es/boja/2013/48/1 |
| Orden de 24 de octubre de 2005 (BOJA 2005/217) | https://www.juntadeandalucia.es/boja/2005/217/4 |
| Resolución de 9 de mayo de 2024 (BOJA 2024/95/52) | https://www.juntadeandalucia.es/boja/2024/95/52 |
| Modelo certificado instalación BT (pdf rellenable) | https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/02/140223_Certificado_BT_rellenable_mod.pdf |
