# Hallazgos LAT — Real Decreto 223/2008, de 15 de febrero, por el que se aprueban el Reglamento sobre condiciones técnicas y garantías de seguridad en líneas eléctricas de alta tensión y sus Instrucciones Técnicas Complementarias ITC-LAT 01 a 09
<!-- Fuente: BOE-A-2008-5269 | Analizado con NotebookLM (prompt cruzado LSE + RD1955 + LPACAP + EIA + D9 + DL2 + RAT) | Revisado manualmente -->

### Sección Reglas del Motor

| **ID-NN** | Descripción | Tipo_solicitud | Fase_afectada | Condición_activación | Excepción_de | Fuente_legal | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LAT-01** | **Sometimiento a autorización** de líneas de conexión y distribución | AAP, AAC, AE | Diseño | `es_ptd` = false AND `tipo_linea_funcional` IN ('generacion', 'consumidor_red', 'linea_directa', 'acometida', 'red_distribucion') | **RAT-01** | Art. 20.1; ITC-LAT 04 §4 | **Restringe a RAT-01**. Mientras RAT exime a instalaciones privadas, LAT obliga a autorizar casi toda línea que conecte con la red. |
| **LAT-02** | **Exención de autorización** para líneas privadas exclusivas | AAP, AAC, AE | Diseño | `tipo_linea_funcional` = 'privada_exclusiva' AND `instalacion_cedida` = false | **LSE-01** | Art. 20.1; ITC-LAT 04 §4 | **Complementa a RAT-01**. Define el único supuesto de línea AT sin autorización sustantiva. |
| **LAT-03** | **Sustitución de inspección por OC** para líneas ≤ 30 kV | AE / Explotación | Post-servicio | `tension_nominal_kv` ≤ 30 | N/A | Art. 21.2 | **Prevalece sobre RAT-03** por especialidad técnica. Permite usar técnicos titulados en lugar de OC para media tensión. |
| **LAT-04** | **Inspección inicial obligatoria por OC** (> 30 kV) | AE | Pre-puesta en servicio | `tension_nominal_kv` > 30 AND `es_ptd` = false | N/A | Art. 20.1.d | **Cubierta por RAT-03**. Requisito de seguridad previo al acta de puesta en servicio. |
| **LAT-05** | **Contrato de mantenimiento obligatorio** para no-PTD | AE | Pre-puesta en servicio | `es_ptd` = false | N/A | Art. 20.1.g | **Cubierta por RAT-04**. Debe suscribirse con empresa instaladora habilitada. |
| **LAT-06** | **Capacidad técnica de PTD** para auto-ejecución | Todas | Registro / Inicio | `es_ptd` = true AND ejecución por medios propios | N/A | Art. 16 | **Cubierta por RAT-05**. Exime de presentar la declaración responsable de instalador (ITC-LAT 03). |
| **LAT-07** | **Uso de Proyectos Tipo** para líneas repetitivas | AAC | Diseño | Instalaciones de PTD o para cesión | N/A | Art. 13.2 | **Complementa a RD1955-01** y **RAT-06**. Deben ser aprobados por la Administración y completados con datos específicos. |
| **LAT-08** | **Resolución de discrepancias** técnico-titular | AAC / AE | Instrucción | Falta de acuerdo sobre adaptación del proyecto a norma | N/A | Art. 20.1; ITC-LAT 04 §4 | **Complementa a LPACAP-05**. El órgano competente resuelve en caso de conflicto entre empresa instaladora y director de obra. |

---

### 1. Plazos — días, silencio administrativo, quién resuelve

*   **Aprobación de especificaciones particulares (PTD):** El plazo para resolver es de **3 meses**, considerándose el silencio administrativo como **positivo** (aprobatorio).
*   **Inspecciones periódicas:** Obligatorias cada **3 años** para todas las líneas.
*   **Vigilancia del sistema de puesta a tierra:** Revisión obligatoria al menos cada **6 años**.
*   **Notificación de accidentes:** El titular debe remitir el informe al órgano competente en un plazo no superior a **3 meses**.
*   **Comunicación de discrepancias técnicas:** La empresa instaladora debe notificar por escrito al director de obra y titular de inmediato; si no hay acuerdo, resuelve la Administración "en el más breve plazo posible".
*   **Silencio Administrativo General:** Se confirma como **desestimatorio** para procedimientos de autorización (AAP, AAC, AE) y transmisión, conforme a la remisión al RD 1955/2000.

---

### 2. Variables

| Variable | Tipo | Naturaleza | Estado | Norma de origen |
| :--- | :--- | :--- | :--- | :--- |
| `es_ptd` | boolean | dato | Ya existe (ver contexto BDDAT) | Art. 16 RD 223/2008 |
| `instalacion_cedida` | boolean | dato | Ya existe (ver contexto BDDAT) | ITC-LAT 04 §5 |
| `tension_nominal_kv` | numérico | dato | Ya existe (ver contexto BDDAT) | Art. 3 RD 223/2008 |
| `tipo_linea_funcional` | enum | dato | Ya existe (ver contexto BDDAT) | ITC-LAT 04 §4 |
| `requiere_inspeccion_inicial_oc` | boolean | calculado | Ya existe (ver [RAT-03]) | Art. 20.1.d |
| `tiene_contrato_mantenimiento` | boolean | derivado_doc | Ya existe (ver [RAT-04]) | Art. 20.1.g |
| `longitud_km` | numérico | dato | Ya existe (ver [EIA-02]) | ITC-LAT 07 §5.6.1 |
| `es_proyecto_tipo` | boolean | dato | Ya existe (ver [RAT-06]) | Art. 13.2 |

---

### 3. Excepciones y regímenes simplificados

*   **Sustitución de Inspección por OC (Art. 21.2):** Para líneas de tensión nominal **≤ 30 kV**, el titular puede sustituir la inspección periódica obligatoria de OC por verificaciones de un **técnico titulado competente** externo a la obra y mantenimiento.
*   **Exención de Autorización para Líneas Privadas (ITC-LAT 04 §4):** Solo las líneas de uso exclusivo que no conectan centrales a la red, ni consumidores a transporte/distribución, ni son redes de distribución, están exentas de AAP/AAC/AE.
*   **Exención de "Declaración Responsable" para PTD (Art. 16):** Las distribuidoras y transportistas no necesitan presentar DR de actividad para ejecutar o mantener líneas de su propiedad por medios propios.
*   **Modificaciones sin proyecto (ITC-LAT 09 §4):** No requieren proyecto (solo registro y certificación anual) las sustituciones de elementos por otros similares, reparaciones menores o adecuación de circuitos de control/BT que no alteren las condiciones originales.

---

### 4. Contradicciones o complementos

*   **Ámbito de Autorización de Instalaciones Privadas (Contradicción con RAT-01):**
    *   **RAT-01 (Art. 20.2 RD 337/2014)** exime a toda instalación no-PTD no cedida.
    *   **LAT-01 (ITC-LAT 04 §4 RD 223/2008)** obliga a autorizar líneas de conexión de generación o consumo aunque sean privadas.
    *   **Prevalencia:** **Gana RD 223/2008** para el objeto "línea", aplicando el criterio de mayor restricción por seguridad de red. El RD 337/2014 rige para subestaciones y centros de transformación privados.
*   **Inspección de Media Tensión (Prevalencia sobre RAT-03):**
    *   **RAT-03 (RD 337/2014)** exige OC para inspecciones de instalaciones no-PTD sin distinguir categoría.
    *   **LAT-03 (Art. 21.2 RD 223/2008)** permite sustituir OC por técnicos titulados en líneas ≤ 30 kV.
    *   **Prevalencia:** **Gana RD 223/2008** para líneas por especialidad. Se mantiene OC obligatorio para centros de transformación (RAT).
*   **Plazo de Cierre (Complemento a LSE-07):**
    *   **LSE-07 (Art. 53.5 LSE)** fija el plazo legal de resolución en 6 meses.
    *   **LAT-05 (Art. 20.1.g)** añade que el cierre requiere acreditar que la instalación queda en estado de seguridad, lo cual RAT (ITC-RAT 23 §1) complementa exigiendo inspección técnica de seccionamiento.
*   **Silencio Administrativo en Especificaciones (Complemento a LPACAP-11):**
    *   **LAT-06 (Art. 15.4)** establece **silencio positivo** en 3 meses para especificaciones de PTD.
    *   **LPACAP-11** impone silencio negativo general.
    *   **Prevalencia:** **Gana RD 223/2008** como norma técnica de organización industrial.