# Estudio de flexibilidad de procesos — procedencia académica del enfoque permisivo

> **Estado:** Cerrado. Carlos dio la investigación por terminada el 2026-11-26.
> **Qué es:** nota de procedencia. Recoge los cuatro artículos académicos con los que Carlos
> contrastó, durante el desarrollo, el enfoque que ya había salido de sus conversaciones con
> Perplexity. No es fuente normativa ni de diseño: no decide nada.
> **Relacionado:** [GUIA_GENERAL.md](../guias/GUIA_GENERAL.md) §Principios fundamentales
> (enfoque permisivo, principio de escape)

---

## 1. Origen (lo que dijo Carlos)

- Con Perplexity llegó a los conceptos de «todo permitido mientras no esté prohibido»,
  estructura por capas y flexibilidad por tipos, que son los que BDDAT tiene hoy. El motor de
  reglas es posterior.
- Durante el desarrollo se preguntó si alguien ya había estudiado esto, y le llegaron estos
  artículos. Los leyó como estudios de las formas de construir un tramitador, de lo
  extremadamente rígido a lo extremadamente flexible, y le confirmaron la necesidad de un
  punto intermedio entre ambas filosofías.
- Los cuatro son «los esenciales». Con ellos da por terminada la investigación.
- El de Pesic y van der Aalst (2006) es el que más le confirmó lo que se estaba gestando.
- Dos tratan de procesos médicos, «el caso de proceso y flujo que requiere la flexibilidad y
  la rigidez combinadas» (comprobado en los textos: el de case handling y el de Mans et al.).
  Recuerda además el ejemplo de FLOWer con un «medical report», que está en el primero.

---

## 2. Los cuatro artículos

En orden cronológico. «Copia del autor» es el PDF que el propio van der Aalst publica en su
web; el DOI es el identificador permanente.

### 2.1 Case handling (2005)

**W.M.P. van der Aalst, M. Weske, D. Grünbauer.** *Case handling: a new paradigm for business
process support.* Data & Knowledge Engineering 53(2), pp. 129–162, Elsevier, 2005.
DOI [10.1016/j.datak.2004.07.003](https://doi.org/10.1016/j.datak.2004.07.003) ·
copia del autor: [p252.pdf](https://www.vdaalst.com/publications/p252.pdf)

Presenta el *case handling* como alternativa al workflow clásico para procesos flexibles e
intensivos en conocimiento: el sistema asiste en lugar de guiar, y la ejecución se centra en
lo que se puede hacer para alcanzar el objetivo del caso y no en un flujo predefinido. Su
«metáfora del cirujano ciego» sitúa el problema en un hospital, donde hacen falta a la vez
flexibilidad operativa y procedimientos bien definidos. El ejemplo con FLOWer incluye
actividades como «Get Medical Report».

### 2.2 Enfoque declarativo (2006)

**M. Pesic, W.M.P. van der Aalst.** *A Declarative Approach for Flexible Business Processes
Management.* En: BPM 2006 Workshops, LNCS 4103, pp. 169–180, Springer, 2006.
DOI [10.1007/11837862_18](https://doi.org/10.1007/11837862_18) ·
copia del autor: [p333.pdf](https://www.vdaalst.com/publications/p333.pdf)

Sostiene que los lenguajes imperativos prescriben cómo trabajar y obligan a sobre-especificar
los procesos, lo que provoca cambios frecuentes. Propone un enfoque declarativo (el lenguaje
ConDec, basado en lógica temporal) que dice qué hay que lograr sin fijar cómo: parte de todas
las posibilidades y las acota con restricciones. Observa que el case handling y los sistemas
adaptativos admiten desviaciones, pero el resultado sigue siendo un modelo imperativo.

### 2.3 Taxonomía de la flexibilidad (2008)

**H. Schonenberg, R. Mans, N. Russell, N. Mulyar, W.M.P. van der Aalst.** *Process
Flexibility: A Survey of Contemporary Approaches.* En: *Advances in Enterprise Engineering I*,
LNBIP, pp. 16–30, Springer, 2008.
DOI [10.1007/978-3-540-68644-6_2](https://doi.org/10.1007/978-3-540-68644-6_2) ·
copia del autor: [p460.pdf](https://www.vdaalst.com/publications/p460.pdf)

Plantea como reto ofrecer flexibilidad y apoyo al proceso a la vez. Sitúa los sistemas en un
rango que va de los que imponen el modelo de forma rígida (workflow) a los que solo se guían
por un modelo implícito (groupware). Propone una taxonomía de cuatro tipos de flexibilidad,
aplicable a modelos imperativos y declarativos: **por diseño, por desviación, por
subespecificación y por cambio**. La usa para evaluar ADEPT1, YAWL, FLOWer y Declare. En el
enfoque declarativo, por defecto todos los caminos están permitidos salvo los que violan una
restricción; las restricciones obligatorias se imponen y las opcionales pueden incumplirse.

### 2.4 Flexibilidad en un hospital (2009)

**R.S. Mans, W.M.P. van der Aalst, N.C. Russell, P.J.M. Bakker.** *Flexibility Schemes for
Workflow Management Systems.* En: *Business Process Management Workshops: BPM 2008
International Workshops, Milán*, LNBIP 17, pp. 361–372, Springer, 2009.
DOI [10.1007/978-3-642-00328-8_36](https://doi.org/10.1007/978-3-642-00328-8_36) ·
copia del autor: [p520.pdf](https://www.vdaalst.com/publications/p520.pdf)

Implementa el proceso diagnóstico de la consulta de oncología ginecológica de un hospital
universitario neerlandés (unas 325 actividades) en YAWL, FLOWer, ADEPT1 y Declare. Concluye
que hace falta usar sistemas distintos, combinados, para cubrir los distintos tipos de proceso
asistencial.

---

## 3. Interpretación (mía, no de Carlos)

Dos correspondencias de ideas que conviene tener a mano. Son una lectura, no una derivación:
ninguno de los artículos describe BDDAT y no se afirma que BDDAT implemente ConDec ni Declare.

- **Enfoque permisivo ↔ modelo declarativo.** El «todo permitido salvo prohibición expresa»
  de [GUIA_GENERAL.md](../guias/GUIA_GENERAL.md) es la misma idea que el «todos los caminos
  permitidos salvo los que violan una restricción» de §2.3.
- **Restricciones obligatorias y opcionales ↔ bloqueo duro y permitir con justificación.**
  Las obligatorias se imponen y las opcionales pueden incumplirse (§2.3), igual que en el
  criterio de salvaguardas del proyecto ([colaboracion.md](../../.claude/rules/colaboracion.md))
  se permite con justificación por defecto y el bloqueo duro se reserva para lo irreversible
  (p. ej. lo ya notificado).

---

## 4. Datos y copias

- Los datos bibliográficos se comprobaron contra los PDF y contra Crossref (2026-11-26).
- Los PDF **no están en el repositorio**: es público y los artículos tienen copyright de
  Elsevier (§2.1) y Springer (§2.2–2.4). Quien los quiera en local los baja de los enlaces.
