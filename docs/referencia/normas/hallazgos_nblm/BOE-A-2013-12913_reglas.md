# Hallazgos EIA — Ley 21/2013, de 9 de diciembre, de evaluación ambiental
<!-- Fuente: BOE-A-2013-12913 | Analizado con NotebookLM (prompt cruzado LSE + RD1955 + LPACAP) | Revisado manualmente -->

### Reglas del Motor de Tramitación (Ley 21/2013)

| **EIA-NN** | Descripción | Tipo_solicitud | Fase_afectada | Condición_activación | Excepción_de | Fuente_legal | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EIA-01** | Evaluación previa obligatoria | AAP | Instrucción | Proyectos en Anexos I o II o con efectos significativos | N/A | Art. 9.1 | **Complementa a LSE-01 y RD1955-01**. El acto de autorización no es válido sin EIA. |
| **EIA-02** | EIA Ordinaria (Líneas AT) | AAP | Instrucción | Tensión ≥ 220 kV AND Longitud > 15 km | N/A | Anexo I, Grupo 3g | Establece el umbral para requerir DIA. Exceptúa líneas íntegramente subterráneas en suelo urbanizado. |
| **EIA-03** | EIA Simplificada (Líneas AT) | AAP | Instrucción | Tensión ≥ 15 kV AND Longitud > 3 km | N/A | Anexo II, Grupo 4b | Establece el umbral para requerir IIA. Incluye capturas por avifauna o proximidad a población. |
| **EIA-04** | Inexistencia de silencio positivo ambiental | AAP | Finalización | Vencimiento de plazos DIA/IIA | Silencio positivo general | Art. 10 | **Complementa a LSE-01 (DA 3ª)**. El silencio nunca equivale a evaluación favorable. |
| **EIA-05** | EIA por afección a Red Natura 2000 | AAP | Instrucción | Afección apreciable directa o indirecta | N/A | Art. 7.2.b | Activa EIA simplificada incluso para proyectos fuera de umbrales de anexos. |
| **EIA-06** | Información pública del EsIA | AAP | Instrucción | Procedimiento ordinario | N/A | Art. 36.1 | **Complementa a RD1955-03**. Plazo no inferior a 30 días hábiles. |
| **EIA-07** | Caducidad de trámites de IP y consultas | AAP | Instrucción | Transcurso de 1 año sin traslado al órgano ambiental | N/A | Art. 33.3 | Obliga a repetir la información pública si el expediente se paraliza. |
| **EIA-08** | Prohibición de EIA a posteriori | AAP | Admisión | Proyectos total o parcialmente ejecutados | N/A | Art. 9.1 | Impide legalizar mediante EIA instalaciones ya construidas sin ella. |
| **EIA-09** | Vigencia de la DIA | AAP | Resolución | 4 años desde publicación sin inicio de ejecución | N/A | Art. 43.1 | **Supera plazos generales**. Tras 4 años (más 2 de prórroga), el promotor debe reiniciar EIA. |

---

### 1. Plazos — Días, silencio administrativo y resolución

*   **Días:** Todos los plazos se entienden como **días hábiles** conforme a la LPACAP.
*   **Silencio Administrativo:** Es estrictamente **negativo** (desestimatorio). La falta de emisión de la DIA o IIA en plazo no equivale a una evaluación favorable.
*   **EIA Ordinaria (DIA):**
    *   **Análisis técnico y formulación:** 4 meses (prorrogables 2 meses más) desde la recepción del expediente completo.
    *   **Información pública:** Mínimo 30 días hábiles.
    *   **Consultas a AAPP:** 30 días hábiles.
*   **EIA Simplificada (IIA):**
    *   **Formulación:** 3 meses desde la recepción de la solicitud.
    *   **Consultas a AAPP e interesados:** 20 días hábiles.
*   **Vigencia:** Tanto la DIA como el IIA tienen una vigencia de **4 años** para el inicio de la ejecución, prorrogables por **2 años** adicionales.
*   **Resolución de prórroga:** El órgano ambiental debe resolver en 3 meses; de lo contrario, se entiende desestimada.

---

### 2. Variables del ContextAssembler

| Variable | Tipo | Naturaleza | Estado | Norma de origen |
| :--- | :--- | :--- | :--- | :--- |
| `longitud_km` | numérico | `dato` | **Nueva** | Anexo I y II Ley 21/2013 |
| `tension_nominal_kv` | numérico | `dato` | **Ya existe (ver LSE-01)** | Anexo I y II Ley 21/2013 |
| `discurre_integra_subterranea` | boolean | `dato` | **Nueva** | Anexo I Gr. 3g y Anexo II Gr. 4b |
| `clasificacion_suelo_lista` | enum | `dato` | **Nueva** | Art. 7.1.a y 7.2.a (escape "suelo urbanizado") |
| `puede_afectar_red_natura_2000` | boolean | `dato` | **Nueva** | Art. 7.2.b |
| `requiere_eia_ordinaria` | boolean | `calculado` | **Ya existe (ver RD1955-10)** | Art. 7.1 Ley 21/2013 |
| `requiere_eia_simplificada` | boolean | `calculado` | **Nueva** | Art. 7.2 Ley 21/2013 |
| `hito_dia_favorable` | boolean | `derivado_doc` | **Ya existe (ver RDL23-01)** | Art. 41 Ley 21/2013 |
| `hito_iia_obtenido` | boolean | `derivado_doc` | **Nueva** | Art. 47 Ley 21/2013 |

---

### 3. Excepciones y regímenes simplificados

*   **Excepción por suelo urbanizado:** Las líneas eléctricas que discurran íntegramente en subterráneo por suelo urbanizado quedan excluidas de los umbrales de EIA ordinaria y simplificada, independientemente de su tensión o longitud.
*   **Proyectos de I+D+i:** Los proyectos destinados a ensayar nuevos métodos o productos con una duración no superior a dos años se someten a evaluación simplificada en lugar de ordinaria.
*   **Exclusión por Defensa o Emergencia:** El órgano sustantivo puede excluir de EIA proyectos con objetivo único de defensa o respuesta a emergencias civiles si la evaluación perjudica dichos fines.
*   **Excepción por proyectos específicos:** El Consejo de Ministros (o el órgano autonómico en Andalucía) puede excluir un proyecto en supuestos excepcionales, debiendo someterlo a una forma alternativa de evaluación.
*   **Red Natura 2000:** No requieren EIA los proyectos que tengan relación directa con la gestión del espacio o que estén previstos como permitidos en su plan de gestión.

---

### 4. Contradicciones o complementos respecto a normas ya analizadas

*   **Silencio Administrativo (Complemento):** El **Art. 10** de la Ley 21/2013 refuerza el carácter desestimatorio establecido en la **LSE (DA 3ª)** y el **RD 1955/2000 (RD1955-01)**, clarificando que en materia ambiental no cabe la estimación por transcurso de plazo.
*   **Plazo de Información Pública (Complemento):** El **RD 1955/2000 (RD1955-03)** exige 30 días. La **Ley 21/2013 (Art. 36.1)** exige "no inferior a 30 días hábiles". Prevalece el carácter **hábil** de la Ley 21/2013 por ser norma posterior y alineada con la **LPACAP**.
*   **Relación con exenciones LSE-05 (Confirmación):** La **LSE-05** exime de autorizaciones a recarga VE > 3.000 kW si no requiere EIA. La **Ley 21/2013** establece los criterios (Anexos I y II) que el titular debe justificar que no cumple para acogerse a dicha exención.
*   **Suspensión de plazos sectoriales (Complemento):** La tramitación de la EIA suspende de facto el plazo de resolución de la AAP del **RD 1955/2000 (Art. 128)**, ya que la DIA es un informe "preceptivo y determinante" (Art. 5.1.e y 41.2), lo cual encaja con la causa de suspensión de la **LPACAP (Art. 22.1.d)**.
*   **Vigencia de trámites (Contradicción):** El RD 1955/2000 no establece caducidad para la información pública realizada. La **Ley 21/2013 (Art. 33.3)** introduce una vigencia de **1 año** para estos trámites. **Gana la Ley 21/2013** por especialidad ambiental y rango jerárquico.