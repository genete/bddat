# Hallazgos RD 1955/2000 — Real Decreto 1955/2000, de 1 de diciembre
<!-- Fuente: BOE-A-2000-24019 | Analizado con NotebookLM (v2, prompt cruzado LSE) | Revisado manualmente -->

### Reglas del Motor de Tramitación (Título VII RD 1955/2000)

| **ID-NN** | Descripción | Tipo_solicitud | Fase_afectada | Condición_activación | Excepción_de | Fuente_legal | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RD1955-01** | Obligatoriedad de autorizaciones | Todas | Todas | Siempre | N/A | Art. 115.1 | **Cubierta por LSE-01**. |
| **RD1955-02** | Tramitación conjunta o coetánea | AAP, AAC | Instrucción | Solicitud promotor | N/A | Art. 115.1 | **Cubierta por LSE-02**. |
| **RD1955-03** | Información pública de 30 días | AAP | Instrucción | Siempre | N/A | Art. 125 | Complementa procedimiento base de la LSE. |
| **RD1955-04** | Conformidad presunta en consultas AAPP | AAP, AAC | Instrucción | Silencio de la administración consultada (30 días) | N/A | Art. 127.2 / 131.1 | Silencio positivo técnico para informes sectoriales. |
| **RD1955-05** | Reducción de consultas en AAC | AAC | Instrucción | `tiene_aap_previa` = true AND NOT `requiere_dup` | Regla 30 días | Art. 131.1 | Reduce el plazo de consultas a 15 días. |
| **RD1955-06** | AE Provisional para pruebas | AE | Resolución | Instalaciones de generación | AE definitiva | Art. 132 bis | Habilita puesta en tensión previa a la explotación comercial. |
| **RD1955-07** | Caducidad de la AAP por inactividad | AAP | Post-resolución | No solicitar AAC en el plazo fijado en la resolución | N/A | Art. 128.4 | La AAP debe incluir un plazo de vigencia para pedir la AAC. |
| **RD1955-08** | Caducidad de la Transmisión | Transmisión | Post-resolución | No formalizar en 6 meses desde el otorgamiento | N/A | Art. 134 | Complementa a **LSE-08** con plazo de ejecución. |
| **RD1955-09** | Informe previo DGPEM | AAP | Instrucción | `es_instalacion_transporte` = true (intra-CCAA) | N/A | Art. 114 | Requisito de informe estatal antes de resolver la CCAA. |
| **RD1955-10** | Modificación Nivel 2 — Solo AAC | Modificación | Diseño | `modificacion_exceso_potencia_pct` ≤ 15% AND NOT `requiere_eia_ordinaria` AND `modificacion_dentro_poligonal_o_sin_expropiacion` | Art. 115.1 (AAP) | Art. 115.2 | Permite saltar la fase AAP en modificaciones de generación que no excedan el umbral. |
| **RD1955-11** | Modificación Nivel 3 — Solo AE | Modificación | Diseño | `modificacion_variacion_tecnica_pct` ≤ 10% AND NOT `requiere_eia` AND NOT `requiere_dup` | Art. 115.1 (AAP+AAC) | Art. 115.3 | Modificación no sustancial; solo requiere AE. Confirma régimen LSE (sección Excepciones LSE). |

---

### 1. Plazos — Días, silencio administrativo y resolución

*   **Silencio Administrativo:** Es **desestimatorio** (negativo) con carácter general para todos los procedimientos (AAP, AAC, AE, Transmisión, Cierre).
*   **Plazos de resolución (Referencia Andalucía):**
    *   **AAP, AAC y Transmisión:** El plazo máximo es de **3 meses**.
    *   **AE (Explotación):** El plazo es de **1 mes** desde la solicitud con certificado final.
    *   **Cierre Definitivo:** **6 meses** (Prevalece LSE-07 sobre los 3 meses del Art. 138 RD 1955/2000).
*   **Consultas sectoriales:** Plazo general de **30 días** (naturales según RD, pero hábiles por LPACAP) con **conformidad presunta** tras el vencimiento.

---

### 2. Variables del ContextAssembler

| Variable | Tipo | Naturaleza | Estado | Norma de origen |
| :--- | :--- | :--- | :--- | :--- |
| `tiene_aap_previa` | boolean | `derivado_doc` | **Nueva** | Art. 131.1 RD 1955/2000 |
| `es_modificacion_instalacion` | boolean | `dato` | **Nueva** | Art. 115 RD 1955/2000 |
| `modificacion_exceso_potencia_pct` | numérico | `calculado` | **Nueva** | Art. 115.2.c RD 1955/2000 |
| `modificacion_variacion_tecnica_pct` | numérico | `calculado` | **Nueva** | Art. 115.3.b RD 1955/2000 |
| `es_instalacion_transporte` | boolean | `dato` | **Nueva** | Art. 114 RD 1955/2000 |
| `requiere_ae_provisional` | boolean | `calculado` | **Nueva** | Art. 132 bis RD 1955/2000 |
| `plazo_ejecucion_transmision_meses` | numérico | `constante` | **Nueva** | Art. 134 RD 1955/2000 |
| `potencia_instalada_mw` | numérico | `dato` | **Ya existe (ver LSE-01)** | Art. 111 RD 1955/2000 |
| `requiere_dup` | boolean | `dato` | **Ya existe (ver LSE-05)** | Art. 143 RD 1955/2000 |

---

### 3. Excepciones y regímenes simplificados

*   **Consultas reducidas (Art. 131.1):** El plazo de consultas a organismos se reduce de 30 a **15 días** si ya existe AAP y no hay cambios sustanciales ni DUP.
*   **Modificaciones No Sustanciales (Art. 115.3):** Las modificaciones que no superen el 10% de potencia, no requieran EIA ni DUP, están **exentas de AAP y AAC**, requiriendo únicamente AE. (Confirma régimen LSE).
*   **Obras preparatorias (Art. 131.9):** Una vez obtenida la **AAP**, el titular puede iniciar acondicionamiento de terreno y vallado sin esperar a la AAC.
*   **Urgencia por suministro (Art. 112.2):** Permite autorizar instalaciones por razones de urgencia sin esperar a la adaptación de planes urbanísticos.

---

### 4. Contradicciones o complementos respecto a normas ya analizadas

*   **Cierre Definitivo (Plazo):**
    *   **Contradicción:** El **Art. 138 RD 1955/2000** establece 3 meses para resolver el cierre.
    *   **Prevalencia:** **LSE-07 (Art. 53.5 LSE)** establece **6 meses**. **Gana LSE** por rango jerárquico y fecha de consolidación.
*   **Autorización de Explotación (Nomenclatura):**
    *   **Complemento:** El RD 1955/2000 (Art. 132) utiliza consistentemente "Autorización de Explotación", alineándose con la **LSE 24/2013** y superando terminologías antiguas de "puesta en servicio".
*   **Silencio Administrativo (DA 3ª LSE vs RD 1955):**
    *   **Complemento:** El RD 1955/2000 no explicitaba el sentido del silencio en todos los trámites; la **DA 3ª de la LSE** confirma su carácter **desestimatorio** para todo el Título VII del RD.
*   **Instalaciones Móviles:**
    *   **Prevalencia:** El RD 1955/2000 no contempla el régimen especial de instalaciones móviles < 2 años. **Prevalece LSE-06** que crea la fase de "Autorización de Implantación".
*   **Infraestructuras Recarga VE:**
    *   **Complemento LSE posterior:** El RD 1955/2000 no contempla el régimen especial VE. **LSE-04** (≤ 3.000 kW, fuera de ámbito) y **LSE-05** (> 3.000 kW sin DUP/EIA, exentas de AAP/AAC/AE) añaden regímenes no previstos en el RD — prevalecen por rango y fecha.
