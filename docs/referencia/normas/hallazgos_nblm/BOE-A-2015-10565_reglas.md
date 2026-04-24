# Hallazgos LPACAP — Ley 39/2015, del Procedimiento Administrativo Común de las Administraciones Públicas
<!-- Fuente: BOE-A-2015-10565 | Analizado con NotebookLM (prompt cruzado LSE + RD1955) | Revisado manualmente -->

Tras el análisis de la **Ley 39/2015 (LPACAP)** y su integración con los hallazgos previos de la **LSE 24/2013** y el **RD 1955/2000** para el sistema BDDAT en Andalucía, se extraen las siguientes reglas y configuraciones:

### Reglas del Motor de Tramitación (LPACAP)

**LPACAP-01**; Obligación de resolver y notificar; Todas; Finalización; Siempre; N/A; Art. 21; **Desplazada por plazos sectoriales** (RD1955-01).
**LPACAP-02**; Suspensión por subsanación; Todas; Inicio/Instrucción; Requerimiento de documentos; N/A; Art. 22.1.a; **Complementa** a todos los procedimientos de BDDAT.
**LPACAP-03**; Suspensión por informe preceptivo; AAP, AAC, Cierre; Instrucción; Solicitud de informe a otro órgano; N/A; Art. 22.1.d; **Complementa** (ej. informe DGPEM en RD1955-09). Máximo 3 meses de suspensión.
**LPACAP-04**; Plazo de notificación de 10 días; Todas; Finalización; Tras dictar resolución; N/A; Art. 40.2; **Aplica directamente**; el plazo de resolución sectorial incluye la notificación.
**LPACAP-05**; Subsanación de solicitud (10 días); Todas; Inicio; Solicitud incompleta; N/A; Art. 68.1; **Aplica directamente**.
**LPACAP-06**; Trámite de audiencia (10-15 días); Todas; Instrucción; Antes de redactar propuesta de resolución; N/A; Art. 82.2; **Aplica directamente**.
**LPACAP-07**; Información pública (mínimo 20 días); AAP; Instrucción; Cuando la naturaleza del procedimiento lo requiera; N/A; Art. 83.2; **Desplazada por RD1955-03** (que fija 30 días).
**LPACAP-08**; Caducidad por inactividad del interesado (3 meses); Todas; Instrucción; Paralización por causa imputable al interesado; N/A; Art. 95.1; **Aplica directamente**.
**LPACAP-09**; Tramitación simplificada (30 días); Todas; Todas; Razones de interés público o baja complejidad; N/A; Art. 96; **Aplica directamente** si se acuerda de oficio o a instancia.
**LPACAP-10**; Cómputo de plazos en días hábiles; Todas; Todas; Plazos señalados por días; N/A; Art. 30.2; **Aplica directamente** en Andalucía (excluye sábados, domingos y festivos).
**LPACAP-11**; Silencio administrativo general; Todas; Finalización; Vencimiento del plazo sin resolución; N/A; Art. 24; **Desplazada por DA 3ª LSE** (LSE-01/RD1955-01) que impone silencio negativo.

---

### 1. Plazos — días, silencio administrativo y resolución

*   **Días hábiles:** Por defecto, todos los plazos en días se entienden hábiles (excluyendo sábados, domingos y festivos).
*   **Plazo de resolución supletorio:** 3 meses si la norma sectorial no fija uno (en AT andaluza, el RD 1955/2000 ya fija plazos específicos).
*   **Plazo de notificación:** Las resoluciones deben notificarse en un máximo de 10 días hábiles desde que se dictan.
*   **Subsanación:** 10 días hábiles para que el interesado aporte documentos faltantes.
*   **Audiencia:** Plazo entre 10 y 15 días hábiles para alegaciones finales.
*   **Información Pública:** Mínimo de 20 días hábiles (aunque en AT prevalecen los 30 días del RD 1955/2000).
*   **Silencio Administrativo:** La LPACAP establece el silencio positivo como regla general, pero esta queda **desplazada** por la normativa sectorial de alta tensión que impone el silencio negativo por afectar al dominio público y seguridad.

---

### 2. Variables del ContextAssembler

*   `dias_subsanacion`: **Nueva**. Entero. Plazo de 10 días para corregir solicitudes (Art. 68.1).
*   `dias_audiencia`: **Nueva**. Entero. Rango de 10-15 días para alegaciones (Art. 82.2).
*   `plazo_caducidad_inactividad_meses`: **Nueva**. Entero. 3 meses de inactividad del interesado (Art. 95.1).
*   `es_dia_habil`: **Nueva**. Boolean. Lógica de calendario (Art. 30.2).
*   `fecha_entrada_registro`: **Ya existe** (implícita en expedientes). Fecha de inicio del cómputo (Art. 21.3.b).
*   `requiere_subsanacion`: **Nueva**. Boolean. Disparador de la fase de subsanación y suspensión del plazo (Art. 22.1.a).

---

### 3. Excepciones y regímenes simplificados

*   **Tramitación Simplificada (Art. 96):** Permite resolver en 30 días si la Administración lo acuerda. En AT es poco frecuente debido a la complejidad técnica, pero el motor debe soportarlo como rama procedimental.
*   **Subsanación y mejora voluntaria (Art. 68.3):** La Administración puede invitar al interesado a mejorar su solicitud, lo cual no es un requerimiento de subsanación obligatorio pero afecta al expediente.
*   **No obligatoriedad de presentar documentos ya aportados (Art. 28.2):** Los interesados tienen derecho a no aportar documentos que ya obren en poder de la Administración, lo que obliga a BDDAT a implementar la consulta interna de expedientes previos.

---

### 4. Contradicciones o complementos respecto a normas ya analizadas

*   **Silencio Administrativo (Contradicción):**
    *   La **LPACAP (Art. 24.1)** establece el silencio positivo como norma general.
    *   La **LSE (DA 3ª)** y el **RD 1955/2000 (Hallazgo RD1955-01)** establecen el silencio **negativo**.
    *   **Prevalencia:** **Gana LSE/RD 1955** por ser norma especial (sectorial) y por la excepción expresa de la LPACAP sobre actividades que dañen el medio ambiente o transfieran facultades de dominio público.
*   **Plazo de Información Pública (Contradicción):**
    *   La **LPACAP (Art. 83.2)** fija un mínimo de 20 días hábiles.
    *   El **RD 1955/2000 (Art. 125)** exige 30 días (hábiles según LPACAP).
    *   **Prevalencia:** **Gana RD 1955/2000** por especialidad procedimental en el sector eléctrico.
*   **Cómputo de Plazos (Complemento):**
    *   El **RD 1955/2000** mencionaba días naturales en redacciones antiguas.
    *   La **LPACAP (Art. 30)** unifica a días **hábiles** salvo ley en contrario.
    *   **Prevalencia:** **LPACAP** gana al ser la norma básica que regula el cómputo de términos administrativos.
*   **Caducidad (Complemento):**
    *   El **RD 1955/2000 (Art. 128.4)** regula la caducidad de la AAP por no pedir la AAC.
    *   La **LPACAP (Art. 95)** regula la caducidad por inactividad general de 3 meses.
    *   **Relación:** Ambos coexisten. La caducidad del RD 1955 es un hito de negocio (vencimiento de derecho), la de la LPACAP es una terminación del expediente por abandono.
*   **Subsanación (Complemento):**
    *   El RD 1955 no detallaba el plazo de subsanación inicial.
    *   La **LPACAP (Art. 68.1)** fija los **10 días** universales, cerrando el hueco procedimental en la admisión de la AAP/AAC.