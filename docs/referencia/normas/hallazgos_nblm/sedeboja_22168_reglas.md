# Hallazgos Decreto 9/2011 — Decreto 9/2011, de 18 de enero, por el que se establecen las normas reguladoras para la tramitación telemática y se crea el Registro Telemático de la Consejería de Economía, Innovación y Ciencia (Junta de Andalucía)
<!-- Fuente: sedeboja_22168 | Analizado con NotebookLM (prompt cruzado LSE + RD1955 + LPACAP + EIA) | Revisado manualmente -->

### Reglas del Motor de Tramitación (Decreto 9/2011)

| **ID-NN** | Descripción | Tipo_solicitud | Fase_afectada | Condición_activación | Excepción_de | Fuente_legal | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **D9-01** | **Exención de información pública** para AT 3ª categoría en suelo urbano | AAP | Instrucción | `tension_nominal_kv` ≤ 30 AND `es_linea_subterranea` (o `es_ct_interior`) AND `es_suelo_urbano_o_urbanizable` AND NOT `requiere_dup` | **RD1955-03** | DA 1ª.1 | **Prevalece sobre RD1955-03** por especialidad autonómica. |
| **D9-02** | **Supresión de publicación en BOP** de la resolución | AAP, AAC, AE | Finalización | Mismas condiciones que D9-01 | **RD1955-01** (en cuanto a publicidad) | DA 1ª.3 | **Complementa a RD1955-01**. Elimina el trámite de publicación de la resolución en el Boletín Provincial. |
| **D9-03** | **Tramitación telemática** de procedimientos de industria y energía | Todas | Todas | Siempre | N/A | Art. 3.Uno | **Complementa a LPACAP-01**. Habilita el cauce digital para toda la tramitación. |
| **D9-04** | **Clasificación de instalaciones industriales** (Grupo I y II) | Todas | Inicio | Según necesidad de autorización previa | N/A | Art. 3.Dos | Define que las instalaciones de AT pertenecen al **Grupo I** (requieren autorización previa). |
| **D9-05** | **Órganos competentes para sanciones** energéticas | Todas | Disciplinaria | Según gravedad de la infracción y cuantía | N/A | Art. 2 | **Complementa al régimen sancionador de la LSE**. |

---

### 1. Plazos — Días, silencio administrativo y resolución

*   **Silencio Administrativo:** El documento confirma que el silencio administrativo es **desestimatorio** (negativo) para los procedimientos de registro e inscripción en régimen especial. 
*   **Plazo de resolución de inscripción (Régimen Especial):** **1 mes** para resolver y notificar el otorgamiento de la condición de instalación acogida a régimen especial e inscripción en registro.
*   **Información Pública:** Se **elimina el plazo de 30 días** para los supuestos que cumplen las condiciones de la DA 1ª. Para el resto de casos, se mantiene lo estipulado en el RD 1955/2000 (30 días).
*   **Quién resuelve:** 
    *   **Delegaciones Provinciales (Territoriales):** Instalaciones en una única provincia.
    *   **Dirección General competente en materia de energía:** Instalaciones que excedan el ámbito de una provincia.

---

### 2. Variables del ContextAssembler

| Variable | Tipo | Naturaleza | Estado | Norma de origen |
| :--- | :--- | :--- | :--- | :--- |
| `tension_nominal_kv` | numérico | `dato` | Ya existe (ver **LSE-01**) | DA 1ª D9/2011 |
| `es_linea_subterranea` | boolean | `dato` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.98)** | DA 1ª D9/2011 |
| `es_ct_interior` | boolean | `dato` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.99)** | DA 1ª D9/2011 |
| `es_suelo_urbano_o_urbanizable` | boolean | `dato` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.100) — pendiente migrar a `clasificacion_suelo_lista` (enum)** | DA 1ª D9/2011 |
| `requiere_dup` | boolean | `dato` | Ya existe (ver **LSE-05**) | DA 1ª D9/2011 |
| `potencia_nominal_kw` | numérico | `dato` | **Renombrar**: coincide con `potencia_instalada_mw` | Art. 4 D9/2011 |

---

### 3. Excepciones y regímenes simplificados

*   **Exención de Información Pública (DA 1ª):** Se documenta como una excepción crítica al procedimiento estándar del **RD 1955/2000 (Art. 125)**. Esta norma la **confirma y aplica específicamente al ámbito andaluz**, reduciendo la carga procedimental para instalaciones de media tensión (≤ 30 kV) en entornos urbanos consolidados sin afección a la propiedad privada (sin DUP).
*   **Exención de Publicación en BOP (DA 1ª.3):** Exime de la obligación de publicar la resolución en el Boletín Oficial de la Provincia (excepción al **Art. 128.3 RD 1955/2000**).
*   **Instalaciones de Categoría A (≤ 10 kW):** Régimen simplificado para fotovoltaica donde la definición técnica se realiza mediante **Memoria Técnica de Diseño** en lugar de proyecto.

---

### 4. Contradicciones o complementos (OBLIGATORIA)

*   **Información Pública (Contradicción con RD1955-03):**
    *   El **RD 1955/2000 (Art. 125)** establece la información pública como un trámite general para la AAP.
    *   El **Decreto 9/2011 (DA 1ª)** suprime este trámite para AT de 3ª categoría subterránea/interior en suelo urbano sin DUP.
    *   **Prevalencia:** **Gana el Decreto 9/2011** por ser norma autonómica dictada en ejercicio de sus competencias de autoorganización de procedimientos no básicos (según se justifica en la exposición de motivos).

*   **Información Pública (Contradicción con LPACAP-07):**
    *   La **LPACAP (Art. 83.2)** fija un mínimo de 20 días hábiles.
    *   El **Decreto 9/2011 (DA 1ª)** elimina el trámite por completo en los supuestos citados.
    *   **Prevalencia:** **Gana el Decreto 9/2011** al amparo de la simplificación administrativa sectorial.

*   **Publicación de Resoluciones (Complemento a RD1955-01):**
    *   El **RD 1955/2000 (Art. 128.3)** exige publicar la resolución en el BOP.
    *   El **Decreto 9/2011 (DA 1ª.3)** exime de este requisito para las instalaciones que cumplen los criterios de simplificación.
    *   **Prevalencia:** **Gana el Decreto 9/2011** en el territorio andaluz por rango de norma especial.

*   **Silencio Administrativo (Confirmación de LSE-01 / DA 3ª LSE):**
    *   La **LSE (DA 3ª)** y el **RD 1955/2000** imponen silencio negativo.
    *   El **Decreto 9/2011 (Art. 13.7)** reitera el carácter **desestimatorio** del silencio para las resoluciones de inscripción en el Registro de Régimen Especial.
    *   **Prevalencia:** **Consenso normativo**; se confirma el silencio negativo en todos los procedimientos de AT en Andalucía.