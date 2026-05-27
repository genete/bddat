# Hallazgos RAT — Real Decreto 337/2014, de 9 de mayo, por el que se aprueban el Reglamento sobre condiciones técnicas y garantías de seguridad en instalaciones eléctricas de alta tensión
<!-- Fuente: BOE-A-2014-6084 | Analizado con NotebookLM (prompt cruzado LSE + RD1955 + LPACAP + EIA + D9 + DL2) | Revisado manualmente -->

### Sección Reglas del Motor

| **ID-NN** | Descripción | Tipo_solicitud | Fase_afectada | Condición_activación | Excepción_de | Fuente_legal | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RAT-01** | **Exención de autorización administrativa** para instalaciones no-PTD no cedidas | AAP, AAC, AE | Diseño / Instrucción | `es_ptd` = false AND `instalacion_cedida` = false | **LSE-01** | Art. 20.2; ITC-RAT 22 §4 | Prevalece sobre LSE-01 por especialidad técnica para instalaciones privadas. |
| **RAT-02** | **Sometimiento a autorización** para instalaciones de terceros que se cedan | AAP, AAC, AE | Diseño | `instalacion_cedida` = true | **RAT-01** | Art. 20.3; ITC-RAT 22 §5 | Complementa a **RD1955-01** y **LAT-11.1**. Obliga al régimen del Título VII RD 1955/2000. |
| **RAT-03** | **Inspección inicial obligatoria por Organismo de Control** | AE | Pre-puesta en servicio | `tension_nominal_kv` > 30 AND `es_ptd` = false | N/A | ITC-RAT 22 §4; ITC-RAT 23 §3 | Complementa a **RD1955-06**. Requisito previo al Certificado de Instalación. |
| **RAT-04** | **Contrato de mantenimiento obligatorio** | AE | Pre-puesta en servicio | `es_ptd` = false | N/A | Art. 13; ITC-RAT 22 §4 | Complementa a **RD1955-06**. Debe mantenerse en vigor durante toda la vida de la instalación. |
| **RAT-05** | **Capacidad técnica de PTD** para auto-ejecución | Todas | Registro / Inicio | `es_ptd` = true AND ejecución por medios propios | N/A | Art. 15 | Complementa a **LPACAP-05**. Exime de presentar la declaración responsable de instalador. |
| **RAT-06** | **Uso de Proyectos Tipo** para instalaciones repetitivas | AAC | Diseño | Instalaciones de PTD o para cesión | N/A | Art. 12.2; ITC-RAT 20 §5 | Complementa a **RD1955-01**. Deben completarse con datos específicos de ubicación. |
| **RAT-07** | **Actuaciones sin necesidad de proyecto** ni autorización | Modificación | Diseño | Sustituciones equivalentes o reparaciones menores (ver lista) | **RD1955-11** | ITC-RAT 20 §4 | Complementa a **RD1955-11**. Requiere solo registro interno y certificación anual. |
| **RAT-08** | **Acuerdo de explotación** para instalaciones privadas integradas | AE / Transmisión | Resolución | Instalación privada integrada en red de PTD | N/A | Art. 19 | Complementa a **RD1955-01**. Obliga a fijar responsabilidades por escrito. |

---

### 1. Plazos — días, silencio administrativo, quién resuelve

*   **Inscripción en registro (Instalaciones no-PTD):** El titular debe presentar la documentación en el plazo de **1 mes** desde el certificado final de obra o inspección inicial.
*   **Resolución de discrepancias técnico-instalador:** La Administración pública competente resolverá en el plazo de **1 mes** si no hay acuerdo sobre la adaptación del proyecto a la norma.
*   **Aprobación de especificaciones particulares de PTD:** El plazo para la aprobación será de **3 meses**, considerándose el silencio administrativo como **positivo** (aprobatorio).
*   **Inspecciones periódicas:** Se realizarán obligatoriamente cada **3 años** por Organismo de Control.
*   **Subsanación de defectos en inspección:** El plazo para la corrección de defectos graves o muy graves no excederá de **6 meses**.
*   **Silencio Administrativo General:** Se confirma como **desestimatorio** para todos los procedimientos de autorización (AAP, AAC, AE), conforme a la normativa sectorial.
*   **Notificación de accidentes:** El propietario debe remitir el informe en un tiempo no superior a **3 meses**.

---

### 2. Variables

| Variable | Tipo | Naturaleza | Estado | Norma de origen |
| :--- | :--- | :--- | :--- | :--- |
| `es_ptd` | boolean | dato | Ya existe (ver contexto BDDAT) | Art. 16.1 RD 337/2014 |
| `instalacion_cedida` | boolean | dato | Ya existe (ver contexto BDDAT) | Art. 20.3 RD 337/2014 |
| `tension_nominal_kv` | numérico | dato | Ya existe (ver contexto BDDAT) | Art. 3 RD 337/2014 |
| `requiere_inspeccion_inicial_oc` | boolean | calculado | **Nueva** | ITC-RAT 23 §3 |
| `tiene_contrato_mantenimiento` | boolean | derivado_doc | **Nueva** | Art. 13; ITC-RAT 22 §4 |
| `es_proyecto_tipo` | boolean | dato | **Nueva** | Art. 12.2 |
| `presion_gas_superior_03_bar` | boolean | dato | **Descartar** — parámetro técnico interno de equipo (GIS/SF6), no procedimental | ITC-RAT 16 §2.2 |
| `distancia_maniobra_exterior_m` | numérico | dato | **Descartar** — parámetro técnico interno de maniobra exterior, no procedimental | ITC-RAT 15 §5.2.5 |

---

### 3. Excepciones y regímenes simplificados

*   **Régimen de Puesta en Servicio Directa (Art. 20.2):** Las instalaciones que no sean de empresas PTD ni vayan a ser cedidas **no requieren AAP, AAC ni AE**, sustituyéndose por un proceso de registro tras la verificación técnica.
*   **Exención de Declaración Responsable para PTD (Art. 15):** Las empresas de producción, transporte y distribución no necesitan presentar DR de actividad para realizar trabajos en sus propias instalaciones.
*   **Pruebas Piloto (ITC-RAT 03 §1):** Se permite la instalación de equipos innovadores para pruebas bajo supervisión del titular **sin expediente técnico ni declaración de conformidad** previa.
*   **Ampliaciones menores (ITC-RAT 20 §4):** Trabajos de sustitución de elementos por otros similares o adecuación de circuitos de control **no precisan proyecto** ni nueva autorización.
*   **Instalaciones Móviles (Art. 2.1):** Permite excepciones en condiciones de acceso, canalizaciones y protección contra incendios si el diseño justifica la seguridad equivalente.

---

### 4. Contradicciones o complementos

*   **Autorización de Instalaciones Privadas (Contradicción con RD1955-01):**
    *   El **RD 1955/2000 (Art. 111)** somete todas las instalaciones al Título VII.
    *   El **RD 337/2014 (Art. 20.2)** exime de autorización a las no-PTD no cedidas.
    *   **Prevalencia:** **Gana RD 337/2014** por ser norma especial técnica que define el ámbito de exclusión de la autorización administrativa sustantiva.
*   **Inspección de Líneas ≤ 30 kV (Contradicción con RD 223/2008):**
    *   El **RD 223/2008 (Art. 21.2)** permite sustituir la inspección por OC por la de un técnico titulado para líneas de 3ª categoría.
    *   El **RD 337/2014 (ITC-RAT 23 §3)** exige siempre Organismo de Control para instalaciones no-PTD sin distinguir categoría.
    *   **Prevalencia:** **Gana RD 223/2008** para líneas y **RD 337/2014** para el resto de instalaciones (subestaciones, CT), aplicando el criterio de especialidad por tipo de activo.
*   **Silencio en Especificaciones de PTD (Prevalencia sobre LPACAP-11):**
    *   La **LPACAP (Art. 24.1)** y la **LSE (DA 3ª)** imponen silencio negativo en procedimientos energéticos.
    *   El **RD 337/2014 (Art. 14.4)** establece **silencio positivo** en 3 meses para la aprobación de especificaciones particulares de distribuidoras.
    *   **Prevalencia:** **Gana RD 337/2014** por ser una norma de organización industrial muy específica no afectada por la reserva de ley de la LSE para autorizaciones de instalaciones.
*   **Plazo de Cierre (Complemento a LSE-07):**
    *   La **LSE-07 (Art. 53.5)** fija 6 meses para resolver cierres.
    *   El **RD 337/2014 (ITC-RAT 23 §1)** añade la obligación de **inspeccionar instalaciones fuera de servicio** no desmanteladas para garantizar el seccionamiento de seguridad.
    *   **Complemento:** RAT añade un hito de seguridad técnica al proceso de cierre legal.