Tras el análisis de la **Ley 24/2013, del Sector Eléctrico (LSE)**, desde la perspectiva del sistema **BDDAT** para la tramitación de expedientes en Andalucía, se extraen las siguientes reglas y datos relevantes:

### Reglas del Motor de Tramitación (Título IX LSE)

**LSE-01** | Obligatoriedad de autorizaciones (AAP, AAC, AE) | Todas | Todas | Siempre (salvo exenciones específicas) | N/A | Art. 53.1 | Marco básico que estructura el sistema.
**LSE-02** | Tramitación conjunta o coetánea de AAP y AAC | AAP, AAC | Instrucción | Solicitud del promotor | N/A | Art. 53.1 | Permite el solape de fases en el motor de reglas.
**LSE-03** | Permisos de acceso y conexión como requisito previo | AAP | Admisión | Instalación de generación | N/A | Art. 53.1.a | Bloquea la obtención de la AAP sin el hito externo de acceso.
**LSE-04** | Exención de autorizaciones para recarga VE ≤ 3.000 kW | AAP, AAC, AE | Todas | `es_infraestructura_recarga_ve` = true AND `potencia_recarga_ve_kw` ≤ 3000 | LSE Art. 53.1 | Art. 53.1 | No generan expediente sectorial de AT.
**LSE-05** | Autorización de implantación para instalaciones móviles | AAP | Diseño | Instalación móvil < 2 años | Excepción de AAP | Art. 53.1.c + Anexo | Sustituye la fase AAP por la de "Implantación".
**LSE-06** | Informe del Operador del Sistema para Cierre | Cierre | Instrucción | Siempre | N/A | Art. 53.5 | Requisito previo para la resolución de cierre definitivo.
**LSE-07** | Transmisión de titularidad previa | Transmisión | Resolución | Siempre | N/A | Art. 53.5 | Requiere autorización administrativa previa para que sea efectiva.

---

### 1. Plazos — Días, silencio administrativo y resolución

*   **Silencio Administrativo:** Es **desestimatorio** (negativo) con carácter general para todos los procedimientos de autorización amparados en la LSE.
*   **Plazo de resolución (Competencia Autonómica/Andalucía):**
    *   **General:** El plazo de resolución es de **3 meses** (según el régimen de referencia del RD 1955/2000 adoptado por Andalucía).
    *   **Cierre Definitivo:** **6 meses** para dictar y notificar la resolución.
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
| `es_instalacion_movil` | boolean | `dato` | **Nueva** | Anexo LSE |
| `periodo_implantacion_meses` | numérico | `dato` | **Nueva** | Art. 53.1.c LSE |
| `es_linea_directa` | boolean | `dato` | **Nueva** (parcialmente en `tipo_linea_funcional`) | Art. 42 LSE |

---

### 3. Excepciones y regímenes simplificados

*   **Instalaciones móviles:** Quedan eximidas de la **Autorización Administrativa Previa (AAP)** si su implantación es transitoria (inferior a 2 años). En su lugar, requieren una **Autorización de Implantación** que se resuelve en **3 meses**.
*   **Infraestructuras de recarga VE:** Las que discurren desde el punto de conexión hasta el punto de recarga están exentas de AAP, AAC y AE si no requieren utilidad pública ni evaluación ambiental.
*   **Cierre unilateral (AGE):** Si transcurren **6 meses** desde la solicitud y el operador del sistema lleva ≥ 3 meses con informe favorable, el titular puede proceder al cierre sin esperar resolución expresa.
*   **Modificaciones no sustanciales:** Pueden quedar exentas de AAP y AAC, requiriendo únicamente **Autorización de Explotación (AE)**.

---

### 4. Contradicciones o complementos respecto a normas ya analizadas

*   **Complemento al RD 1955/2000:** La LSE eleva a rango de Ley la estructura de autorizaciones (AAP, AAC, AE) y confirma la prevalencia del silencio negativo sobre el régimen general de la LPACAP.
*   **Contradicción Potencial en Cierre:** El RD 1955/2000 establece un plazo de resolución de **3 meses** para cierres, mientras que la LSE (art. 53.5) especifica **6 meses**. En BDDAT debe prevalecer el plazo de la LSE por rango jerárquico y fecha de consolidación.
*   **Complemento al Decreto 9/2011 (Andalucía):** Mientras que el Decreto 9/2011 simplifica la *información pública* para AT de 3ª categoría, la LSE permite la exención total de autorizaciones para infraestructuras de recarga VE hasta 3.000 kW, independientemente de la tensión.
*   **Definición de Potencia Fotovoltaica:** Se consolida la definición de potencia instalada como el valor mínimo entre la suma de módulos (DC) y la suma de inversores (AC), afectando a los umbrales de competencia (AGE > 50 MW).