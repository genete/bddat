# Hallazgos LSE — Ley 24/2013, del Sector Eléctrico
<!-- Fuente: BOE-A-2013-13645 | Analizado con NotebookLM | Revisado manualmente -->

### Reglas del Motor de Tramitación (Título IX LSE)

**LSE-01** | Obligatoriedad de autorizaciones (AAP, AAC, AE) | Todas | Todas | Siempre (salvo exenciones específicas) | N/A | Art. 53.1 | Marco básico que estructura el sistema.
**LSE-02** | Tramitación conjunta o coetánea de AAP y AAC | AAP, AAC | Instrucción | Solicitud del promotor | N/A | Art. 53.1 | Permite el solape de fases en el motor de reglas.
**LSE-03** | Permisos de acceso y conexión como requisito previo | AAP | Admisión | Instalación de generación | N/A | Art. 53.1.a | Bloquea la obtención de la AAP sin el hito externo de acceso.
**LSE-04** | Exclusión del régimen de autorizaciones para infraestructuras recarga VE ≤ 3.000 kW | Todas | Todas | `potencia_recarga_ve_kw` ≤ 3.000 | Art. 53 completo | Art. 53.1 | Las estaciones ≤ 3.000 kW quedan fuera del ámbito del artículo — no generan expediente sectorial AT.
**LSE-05** | Exención de autorizaciones para infraestructuras recarga VE > 3.000 kW sin DUP ni EIA | AAP, AAC, AE | Todas | `potencia_recarga_ve_kw` > 3.000 AND NOT `requiere_eia` AND NOT `requiere_dup` | AAP, AAC, AE | Art. 53.1 (párrafo exención) | Solo requieren proyecto de ejecución + declaración responsable antes de energizar. El titular debe justificar que no está en el ámbito de la Ley 21/2013.
**LSE-06** | Autorización de implantación para instalaciones móviles | AAP | Diseño | Instalación móvil < 2 años | Excepción de AAP | Art. 53.1.c + Anexo | Sustituye la fase AAP por la de "Implantación".
**LSE-07** | Informe del Operador del Sistema para Cierre | Cierre | Instrucción | Siempre | N/A | Art. 53.5 | Requisito previo para la resolución de cierre definitivo.
**LSE-08** | Transmisión de titularidad previa | Transmisión | Resolución | Siempre | N/A | Art. 53.5 | Requiere autorización administrativa previa para que sea efectiva.

---

### 1. Plazos — Días, silencio administrativo y resolución

*   **Silencio Administrativo:** Es **desestimatorio** (negativo) con carácter general para todos los procedimientos de autorización amparados en la LSE.
*   **Plazo de resolución (Competencia Autonómica/Andalucía):**
    *   **General:** El plazo de resolución es de **3 meses** (según el régimen de referencia del RD 1955/2000 adoptado por Andalucía).
    *   **Cierre Definitivo:** **6 meses** para dictar y notificar la resolución. ⚠️ Prevalece sobre los 3 meses del RD 1955/2000 por rango jerárquico y fecha de consolidación.
*   **Plazo de resolución (Competencia Estatal - AGE):** **1 año** para dictar resolución expresa (silencio desestimatorio).
*   **Quién resuelve:**
    *   **Junta de Andalucía:** Instalaciones de producción ≤ 50 MW y redes de distribución íntegramente en su territorio.
    *   **Administración General del Estado:** Instalaciones > 50 MW, transporte primario y acometidas ≥ 380 kV.
*   **Reposición del suministro:** Una vez pagada la deuda, la empresa debe reponer el suministro en **24 horas**.

---

### 2. Variables del ContextAssembler

| Variable | Tipo | Naturaleza | Estado en ContextAssembler | Norma de origen |
| :--- | :--- | :--- | :--- | :--- |
| `potencia_instalada_mw` | numérico | `dato` | **Ya existe** | Art. 3.13.a LSE |
| `potencia_recarga_ve_kw` | numérico | `dato` | **Ya existe** | Art. 53.1 LSE |
| `es_infraestructura_recarga_ve` | boolean | `dato` | **Ya existe** | Art. 53.1 LSE |
| `requiere_dup` | boolean | `dato` | **Verificar** | Art. 53.1 LSE (párrafo exención VE) |
| `es_instalacion_movil` | boolean | `dato` | **Nueva** | Anexo LSE |
| `periodo_implantacion_meses` | numérico | `dato` | **Nueva** | Art. 53.1.c LSE |
| `es_linea_directa` | boolean | `dato` | **Nueva** (parcialmente en `tipo_linea_funcional`) | Art. 42 LSE |

---

### 3. Excepciones y regímenes simplificados

*   **Infraestructuras recarga VE ≤ 3.000 kW:** Quedan **fuera del ámbito** del Art. 53 — no generan expediente de autorización AT.
*   **Infraestructuras recarga VE > 3.000 kW sin DUP ni EIA:** Dentro del ámbito pero **exentas de AAP, AAC y AE**. Solo requieren proyecto de ejecución + declaración responsable antes de energizar, justificando que no están en el ámbito de la Ley 21/2013.
*   **Instalaciones móviles:** Exentas de AAP si la implantación es transitoria (< 2 años). Requieren "Autorización de Implantación" (3 meses).
*   **Modificaciones no sustanciales:** Exentas de AAP y AAC, requieren únicamente AE.
*   **Cierre unilateral (AGE):** Si transcurren 6 meses desde la solicitud y el operador del sistema lleva ≥ 3 meses con informe favorable, el titular puede proceder al cierre sin resolución expresa.
*   **I+D+i:** El Gobierno puede eximir de AAP y AAC si el proyecto está exento de EIA y acreditado por convocatoria estatal/europea o por la Secretaría de Estado de Energía.

---

### 4. Contradicciones o complementos respecto a normas ya analizadas

*   **Complemento al RD 1955/2000:** La LSE eleva a rango de Ley la estructura de autorizaciones (AAP, AAC, AE) y confirma la prevalencia del silencio negativo sobre el régimen general de la LPACAP.
*   **Contradicción resuelta — Cierre:** El RD 1955/2000 establece 3 meses para cierres; la LSE (art. 53.5) especifica 6 meses. Prevalece la LSE por rango jerárquico y fecha de consolidación.
*   **Complemento al Decreto 9/2011:** El Decreto 9/2011 simplifica la información pública para AT de 3ª categoría; la LSE añade la exención total para infraestructuras VE > 3.000 kW sin DUP ni EIA, independientemente de la tensión.
*   **Definición de Potencia Fotovoltaica:** Se consolida como el mínimo entre suma de módulos (DC) y suma de inversores (AC), afectando a los umbrales de competencia (AGE > 50 MW).
