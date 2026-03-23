# Recursos del Portal de Desarrollo — Junta de Andalucía

> Fuente: https://desarrollo.juntadeandalucia.es/recursos/buscador
> Fecha de consulta: 2026-03-03
> Alcance: 136 recursos catalogados (sistemas de información, normas, guías, APIs, plataformas, etc.)

Este documento clasifica los recursos publicados por la Agencia Digital de Andalucía que son relevantes para el proyecto **BDDAT** (sistema de tramitación de expedientes de autorización de instalaciones de alta tensión).

---

## Índice

1. [Alta relevancia — Integración directa o cumplimiento obligatorio](#1-alta-relevancia)
   - [Autenticación y firma electrónica](#11-autenticación-y-firma-electrónica)
   - [Tramitación y expedientes](#12-tramitación-y-expedientes)
   - [Registro, notificación y ventanilla ciudadana](#13-registro-notificación-y-ventanilla-ciudadana)
   - [Gestión de usuarios y verificación documental](#14-gestión-de-usuarios-y-verificación-documental)
   - [Normas y guías de cumplimiento obligatorio](#15-normas-y-guías-de-cumplimiento-obligatorio)
   - [Cláusulas PPT aplicables](#16-cláusulas-ppt-aplicables)
2. [Media relevancia — Integración en fases futuras](#2-media-relevancia)
3. [Baja relevancia — Fuera del alcance actual](#3-baja-relevancia)
4. [Resumen ejecutivo](#4-resumen-ejecutivo)

---

## 1. Alta relevancia

### 1.1 Autenticación y firma electrónica

Recursos críticos para el cumplimiento del ENS y la Ley 39/2015 en producción.

| Recurso | Descripción | Ficha |
|---------|-------------|-------|
| **@firma** | Plataforma corporativa de autenticación y firma basada en certificados electrónicos | [/recursos/activo/afirma](https://desarrollo.juntadeandalucia.es/recursos/activo/afirma) |
| **SSOWEB** | Servicio Centralizado de Autenticación Única (SSO) para aplicaciones web corporativas | [/recursos/activo/ssoweb](https://desarrollo.juntadeandalucia.es/recursos/activo/ssoweb) |
| **PROXYCL@VE** | Servicio Centralizado de Intermediación con Cl@ve para autenticación de ciudadanos | [/recursos/activo/proxy-clave](https://desarrollo.juntadeandalucia.es/recursos/activo/proxy-clave) |
| **Port@firmas** | Port@firmas corporativo para firma de resoluciones y documentos administrativos | [/recursos/activo/portafirmas](https://desarrollo.juntadeandalucia.es/recursos/activo/portafirmas) |
| **AutoFirma** | Aplicación de escritorio/navegador para firma electrónica del ciudadano y tramitador | [/recursos/activo/autofirma](https://desarrollo.juntadeandalucia.es/recursos/activo/autofirma) |
| **Sellado de tiempo** | Plataforma de sellado temporal de documentos firmados electrónicamente | [/recursos/activo/sellado-tiempo](https://desarrollo.juntadeandalucia.es/recursos/activo/sellado-tiempo) |
| **AsistE** | Identificación y firma por Funcionario Habilitado en oficinas de asistencia en materia de registro | [/recursos/activo/asiste](https://desarrollo.juntadeandalucia.es/recursos/activo/asiste) |

**Nota:** @firma + SSOWEB/PROXYCL@VE es la combinación obligatoria para autenticación corporativa e-administración en la JdA. El sellado de tiempo es requerimiento habitual en tramitación sometida a ENS.

---

### 1.2 Tramitación y expedientes

Sistemas corporativos con funcionalidad análoga o complementaria a BDDAT.

| Recurso | Descripción | Ficha |
|---------|-------------|-------|
| **TeJA** | Tramitador de expedientes genérico corporativo de la JdA | [/recursos/activo/teja](https://desarrollo.juntadeandalucia.es/recursos/activo/teja) |
| **Trew@** | Motor de tramitación corporativo — referencia para el motor de reglas de BDDAT | [/recursos/activo/trewa](https://desarrollo.juntadeandalucia.es/recursos/activo/trewa) |
| **PTw@ndA** | Plataforma de Tramitación w@ndA — contexto arquitectónico de la tramitación electrónica JdA | [/recursos/activo/ptwanda](https://desarrollo.juntadeandalucia.es/recursos/activo/ptwanda) |
| **ARCO** | Gestión integrada de documentos y expedientes electrónicos | [/recursos/activo/arco](https://desarrollo.juntadeandalucia.es/recursos/activo/arco) |
| **Inform@** | Tramitación electrónica de expedientes de emisión de informes a organismos consultados | [/recursos/activo/informa](https://desarrollo.juntadeandalucia.es/recursos/activo/informa) |
| **HRE** | Herramienta de Remisión de Expedientes entre unidades administrativas | [/recursos/activo/hre](https://desarrollo.juntadeandalucia.es/recursos/activo/hre) |
| **ReJA** | Gestión electrónica de recursos administrativos (alzada, reposición, revisión) | [/recursos/activo/reja](https://desarrollo.juntadeandalucia.es/recursos/activo/reja) |
| **@rchiva** | Sistema de Información de Archivos — archivo definitivo de expedientes resueltos | [/recursos/activo/archiva](https://desarrollo.juntadeandalucia.es/recursos/activo/archiva) |

**Nota clave:** TeJA, Trew@ y PTw@ndA son los equivalentes corporativos de BDDAT. Conviene documentar la justificación del desarrollo sectorial propio frente a estos sistemas, o evaluar si BDDAT puede construirse como módulo encima de alguno de ellos.

**Inform@** es especialmente relevante para el issue #153 (consultas a organismos en separatas): gestiona exactamente el tipo de trámite de solicitud de informe a terceros que aparece en los expedientes AT.

---

### 1.3 Registro, notificación y ventanilla ciudadana

| Recurso | Descripción | Ficha |
|---------|-------------|-------|
| **@RIES** | Registro telemático unificado — registro de entrada/salida de solicitudes de autorización AT | [/recursos/activo/aries](https://desarrollo.juntadeandalucia.es/recursos/activo/aries) |
| **Notific@** | Prestador de servicios de notificación electrónica a titulares (obligatorio Ley 39/2015) | [/recursos/activo/notifica](https://desarrollo.juntadeandalucia.es/recursos/activo/notifica) |
| **VEAJA** | Ventanilla Electrónica de la Administración de la JdA — canal de entrada de solicitudes | [/recursos/activo/veaja](https://desarrollo.juntadeandalucia.es/recursos/activo/veaja) |
| **VEA** | Componente reutilizable de Ventanilla Electrónica para presentación de solicitudes | [/recursos/activo/vea](https://desarrollo.juntadeandalucia.es/recursos/activo/vea) |
| **Carpeta Ciudadana** | App ciudadanía: los titulares AT podrían consultar sus expedientes, notificaciones y certificados | [/recursos/activo/carpeta-ciudadana](https://desarrollo.juntadeandalucia.es/recursos/activo/carpeta-ciudadana) |
| **SCSP** | Supresión de Certificados en Soporte Papel — consulta de datos en otras AA.PP. sin exigir certificados al ciudadano | [/recursos/activo/scsp](https://desarrollo.juntadeandalucia.es/recursos/activo/scsp) |

**Nota:** El trío **@RIES + Notific@ + Port@firmas** es el núcleo estándar de cualquier tramitación electrónica en la JdA conforme a la Ley 39/2015.

---

### 1.4 Gestión de usuarios y verificación documental

| Recurso | Descripción | Ficha |
|---------|-------------|-------|
| **GUIA** | Sistema de Gestión Unificada de Identidades de la JdA — directamente aplicable al modelo de roles (ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO) | [/recursos/activo/guia](https://desarrollo.juntadeandalucia.es/recursos/activo/guia) |
| **HCV** | Herramienta Centralizada de Verificación de documentos | [/recursos/activo/hcv](https://desarrollo.juntadeandalucia.es/recursos/activo/hcv) |
| **Compuls@** | Expedición de copias autenticadas electrónicamente de documentos en papel | [/recursos/activo/compulsa](https://desarrollo.juntadeandalucia.es/recursos/activo/compulsa) |
| **RPS** | Registro de Procedimientos y Servicios — el procedimiento de autorización AT debe estar catalogado aquí | [/recursos/activo/rps](https://desarrollo.juntadeandalucia.es/recursos/activo/rps) |

---

### 1.5 Normas y guías de cumplimiento obligatorio

Documentos normativos que aplican directamente al desarrollo y despliegue de BDDAT.

| Recurso | Ficha |
|---------|-------|
| **Norma para el desarrollo seguro** (ENS) | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/norma-para-el-desarrollo-seguro) |
| **Norma para la definición y publicación de APIs** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/norma-para-la-definicion-publicacion-apis) |
| **Norma de alineamiento con la pila tecnológica de la ADA** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/norma-alineamiento-pila-tecnologica) |
| **Guía de desarrollo de APIs** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/guia-desarrollo-apis) |
| **Guía técnica de integración de APIs** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/guia-tecnica-integracion-apis) |
| **Guía de integración de Interoperabilidad** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/guia-integracion-interoperabilidad) |
| **Arquitectura de referencia en APIs** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/arquitectura-referencia-en-apis) |
| **Arquitectura de referencia — Seguridad** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/arquitectura-referencia-seguridad) |
| **Arquitectura de referencia — Interoperabilidad** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/arquitectura-referencia-en-interoperabilidad) |
| **Guía sobre la política de seguridad para interoperabilidad de servicios** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/guia-sobre-la-politica-seguridad-para-interoperabilidad-servicios-su) |
| **Norma de usabilidad en sitios web** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/norma-usabilidad-en-sitios-web) |
| **Norma para la gestión de datos** | [enlace](https://desarrollo.juntadeandalucia.es/recursos/reglas-pautas/norma-para-la-gestion-datos) |

**Acción requerida:** La *Norma de alineamiento con la pila tecnológica de la ADA* determinará si el stack Python/Flask/PostgreSQL de BDDAT está homologado o requiere justificación de excepción.

---

### 1.6 Cláusulas PPT aplicables

Si BDDAT fue objeto de licitación o contrato, estas cláusulas son de aplicación directa en el pliego:

| Cláusula | Aplicabilidad en BDDAT |
|----------|------------------------|
| **Ciberseguridad** | BDDAT sometido a ENS |
| **Gestión de usuarios y control de accesos** | Modelo de roles (ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO) |
| **Uso de certificados y firma electrónica** | Firma de resoluciones y documentos en expedientes AT |
| **Definición de procedimientos administrativos por medios electrónicos** | BDDAT implementa un procedimiento administrativo electrónico completo |
| **Rediseño funcional y simplificación de procedimientos** | Flujos de tramitación: solicitudes, fases, trámites, tareas |
| **Interoperabilidad** | Integraciones con @firma, SCSP, Notific@, etc. |
| **Accesibilidad de sitios web** | BDDAT es aplicación web JdA — cumplimiento RD 1112/2018 |
| **Verificación de documentos firmados electrónicamente** | BDDAT gestiona documentos firmados (proyectos, resoluciones) |

---

## 2. Media relevancia

Recursos útiles en fases futuras o contextos concretos.

| Recurso | Categoría | Descripción | Relevancia |
|---------|-----------|-------------|------------|
| **Formul@** | Utilidad | Generador de formularios | Formularios de solicitud de autorización AT |
| **Model@** | Utilidad | Herramienta de modelado de procedimientos | Documentar el procedimiento AT implementado en BDDAT |
| **Servicio WS-CDAU** | API | Normalización y geocodificación de direcciones | Localización geográfica de las instalaciones AT |
| **Gestión de citas y turnos** (Tu Turno) | Sistema | Gestión corporativa de citas en oficinas | Citas presenciales para inspecciones o entrega de documentación |
| **BandeJA** | Sistema | Comunicaciones interiores electrónicas | Comunicación interna entre tramitadores, supervisores y organismos |
| **Microsoft Purview** | Plataforma | Gobierno del dato corporativo | Integración en estrategia de datos de la JdA |
| **Plataforma CI/CD corporativa** | Plataforma | Despliegue continuo corporativo | Despliegue de BDDAT en infraestructura JdA |
| **HRC** | Utilidad | Herramienta de Registro de la Calidad | Métricas de calidad en entrega formal del proyecto |
| **Oficina de Arquitectura** | Servicio de apoyo | Soporte de arquitectura de soluciones | Validar el diseño técnico de BDDAT en el contexto corporativo |
| **Oficina de Interoperabilidad** | Servicio de apoyo | Asesoría en interoperabilidad | Soporte para integrar BDDAT con plataformas corporativas |
| **Certif. servidor y sello** | Servicio de apoyo | Gestión de certificados electrónicos de servidor | Certificado TLS en producción y sello para firma de resoluciones |
| **Arq. ref. — Observabilidad** | Arquitectura | Monitorización y trazabilidad | Relevante en producción a largo plazo |

---

## 3. Baja relevancia

Recursos fuera del alcance actual de BDDAT (se omiten detalles):

- **Arquitecturas de referencia** de microservicios, EDA, microfrontend, SPA, data lake — BDDAT usa arquitectura monolítica Flask/Jinja2.
- **Frameworks Java** (ada-fwk-ms, ada-fwk-webapps) — stack distinto.
- **Normas para Java, microservicios, microfrontends, SPA, CaaS, cloud-native** — no aplican al stack actual.
- **Recursos de geoinformación** (IDEAndalucía, SIG Corporativo, CDAU, Mapea, Geodesia...) — solo si se añade localización geográfica de instalaciones AT.
- **Plataformas analíticas** (PowerBI, Tableau, SAVIA) — explotación estadística futura, no en Fase 2.
- **Normas DevSecOps / CI/CD / repositorios corporativos** — relevantes en integración con infraestructura corporativa, no en Fase 2.
- **Cláusulas PPT sobre apertura de datos/servicios** — datos administrativos reservados.

---

## 4. Resumen ejecutivo

### Para producción (integración obligatoria)

El conjunto mínimo para que BDDAT opere conforme al marco corporativo de la JdA y la Ley 39/2015:

```
@RIES           → Registro de entrada de solicitudes AT
Notific@        → Notificaciones electrónicas a titulares
Port@firmas     → Firma de resoluciones y documentos
@firma/SSOWEB   → Autenticación corporativa (tramitadores internos)
PROXYCL@VE      → Autenticación ciudadanos vía Cl@ve (si hay acceso externo)
SCSP            → Verificación de datos sin exigir certificados al ciudadano
HCV             → Verificación documental
Sellado tiempo  → Sellado temporal de documentos firmados
```

### Norma urgente a revisar

La **Norma de alineamiento con la pila tecnológica de la ADA** determinará si Python/Flask/PostgreSQL está homologado en la JdA o si hay que justificar una excepción formal.

### Decisión arquitectónica pendiente

**TeJA, Trew@ y PTw@ndA** cubren el mismo dominio que BDDAT. Conviene documentar por qué BDDAT se desarrolla como aplicación sectorial propia (especificidad del dominio AT, integración con normativa eléctrica específica, necesidad de motor de reglas sectorial) en lugar de extender alguna de estas plataformas. Esta justificación será necesaria ante la Oficina de Arquitectura.

### Próximos pasos sugeridos

1. Consultar la ficha de **Trew@** y **PTw@ndA** para evaluar capacidad de reutilización.
2. Leer la **Norma de alineamiento tecnológico** y la **Norma de desarrollo seguro** antes del despliegue.
3. Contactar con la **Oficina de Interoperabilidad** para planificar la integración con @RIES + Notific@ + Port@firmas.
4. Registrar el procedimiento de autorización AT en **RPS**.
5. Revisar **Inform@** para el issue #153 (consultas a organismos).
