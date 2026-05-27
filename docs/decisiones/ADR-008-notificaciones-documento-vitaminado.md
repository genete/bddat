# ADR-008 — Tabla `notificaciones` como documento vitaminado para la tarea NOTIFICAR

**Estado:** Adoptada
**Fecha:** 2026-05-17
**Issue:** #418

---

## Contexto

La tarea NOTIFICAR produce un justificante (JUSTIFICANTE_NOTIFICA, JUSTIFICANTE_BANDEJA,
JUSTIFICANTE_SIR o JUSTIFICANTE_POSTAL) y el sistema necesita tres datos estructurados
adicionales que el documento plano no puede capturar:

1. **Resultado**: ¿fue la notificación correcta o caducó? (LPACAP arts. 40-44)
2. **Número de intento**: ¿es el primer intento o el segundo? La LPACAP exige un
   máximo de 2 intentos; al tercero el procedimiento obliga a publicar en BOE/BOJA.
3. **Fecha del intento**: ancla el cómputo de suspensiones de plazos (LPACAP art. 22).

### Diseño previo y sus defectos

Se crearon tres tablas genéricas para cubrir esta necesidad:

- `tipos_resultado_documentos` — catálogo: CORRECTA / INCORRECTA / INDIFERENTE
- `tipos_documentos_resultados_validos` — whitelist N:M por tipo de documento
- `resultados_documentos` — instancia: resultado de cada documento concreto

**Defecto 1 — Semántica invertida.**
El resultado se atribuye al documento (la evidencia) en lugar de a la acción
(la notificación). La tarea NOTIFICAR no tiene campo `resultado` propio; la Fase
sí tiene `resultado_fase_id`. El diseño es inconsistente con el patrón del proyecto.

**Defecto 2 — Whitelist encubierta.**
`tipos_documentos_resultados_validos` es una whitelist positiva que contradice el
principio del motor (blacklist — todo permitido salvo lo expresamente bloqueado)
adoptado en ADR-007. Requería seeds de mantenimiento periódico (el issue #378 era
exactamente eso) y duplica responsabilidades entre el catálogo y el motor.

**Defecto 3 — Violación del patrón "documento vitaminado".**
ADR-005 estableció que cuando un documento necesita estructura propia se le añade
tabla vitaminada. El caso paradigmático es `diagnosticos` para la tarea ANALIZAR.
Los justificantes de notificación tienen la misma necesidad y deben seguir el mismo
patrón.

### Patrón establecido en el proyecto

| Tarea       | Documento producido | Tabla vitaminada  | Resultado                               |
|-------------|---------------------|-------------------|-----------------------------------------|
| ANALIZAR    | DIAGNOSTICO         | `diagnosticos`    | Implícito en el contenido del diagnóstico |
| NOTIFICAR   | JUSTIFICANTE_*      | `notificaciones`  | Campo `resultado` explícito             |

---

## Decisión

Crear tabla `notificaciones` como documento vitaminado para los justificantes de la
tarea NOTIFICAR. Eliminar simultáneamente las tres tablas del diseño previo, que en
el momento de la decisión están vacías.

### Schema de `notificaciones`

```sql
CREATE TABLE public.notificaciones (
    id                  SERIAL PRIMARY KEY,
    documento_id        INTEGER NOT NULL UNIQUE
                            REFERENCES public.documentos(id) ON DELETE CASCADE,
    resultado           VARCHAR(12) NOT NULL
                            CHECK (resultado IN ('CORRECTA', 'INCORRECTA')),
    canal               VARCHAR(10) NOT NULL
                            CHECK (canal IN ('NOTIFICA', 'BANDEJA', 'SIR', 'POSTAL')),
    fecha_notificacion  DATE NOT NULL,
    numero_intento      SMALLINT NOT NULL DEFAULT 1
                            CHECK (numero_intento IN (1, 2)),
    observaciones       TEXT
);
```

**Notas de diseño:**

- `UNIQUE(documento_id)`: un justificante = una notificación. No hay resultado
  ambiguo — la relación es 1:1.
- `resultado` excluye INDIFERENTE: el acto de notificar termina en resultado binario
  (se practicó o caducó/falló). INDIFERENTE era un comodín del diseño anterior
  para documentos sin resultado. Si no hay fila en `notificaciones`, la tarea
  simplemente no tiene resultado registrado — su significado natural.
- `canal` está redundado con `tipo_documento` del justificante, pero se incluye
  para que el motor y los informes puedan consultarlo sin join adicional a
  `tipos_documentos`.
- `numero_intento`: habilita la lógica LPACAP de dos intentos. La regla concreta
  del motor (ADVERTIR o BLOQUEAR al segundo INCORRECTA) se implementa en el issue
  de implementación.

### Tablas eliminadas

- `tipos_resultado_documentos`
- `tipos_documentos_resultados_validos`
- `resultados_documentos`

### Código afectado

| Fichero | Cambio |
|---------|--------|
| `app/models/notificaciones.py` | Nuevo modelo `Notificacion` |
| `app/models/tipos_resultado_documentos.py` | Eliminar |
| `app/models/tipos_documentos_resultados_validos.py` | Eliminar |
| `app/models/resultados_documentos.py` | Eliminar |
| `app/models/__init__.py` | Añadir `Notificacion`, eliminar 3 imports |
| `app/models/tareas.py` | Property `resultado`: leer de `notificaciones` |
| `app/models/tramites.py` | Property `finalizado`: leer de `notificaciones` |
| `app/services/invariantes_esftt.py` | `_check_finalizar_fase` y `_check_finalizar_tramite`: join a `Notificacion` |

---

## Razonamiento

**Por qué no añadir `resultado` directamente a `tareas`.**
El resultado de la notificación es una propiedad del acto materializado en el
justificante, no de la tarea administrativa. La tarea tiene estados propios
(PLANIFICADA/EN_CURSO/EJECUTADA) distintos del resultado del acto. Además, el
justificante puede sustituirse (PDF corregido) sin re-crear la tarea. Vitaminar
el documento mantiene la flexibilidad y la trazabilidad documental.

**Por qué eliminar `tipos_documentos_resultados_validos`.**
La tabla es una whitelist positiva: para el tipo X, los resultados válidos son Y.
Esa lógica puede vivir en el modelo o en la UI sin tabla de catálogo. Mantenerla
sería acumular deuda de diseño contra ADR-007 sin beneficio observable.

**Por qué INDIFERENTE queda fuera del CHECK.**
INDIFERENTE no es un resultado del acto de notificar; es la ausencia de resultado.
La semántica correcta es: sin fila en `notificaciones` = resultado no registrado.
Forzar al técnico a elegir entre CORRECTA, INCORRECTA e INDIFERENTE añadiría
ambigüedad operativa sin base normativa.

---

## Consecuencias

- La regla "tarea NOTIFICAR con INCORRECTA bloquea cierre de trámite/fase" sigue
  vigente, ahora legible directamente desde `notificaciones.resultado`.
- El cálculo de suspensiones de plazos (art. 22 LPACAP) puede usar
  `notificaciones.fecha_notificacion` en lugar de deducirla de `fecha_administrativa`
  del documento.
- El servicio de seguimiento puede añadir el estado `PENDIENTE_RESULTADO_NOTIFICACION`
  para distinguir "falta justificante" de "falta registrar resultado". Decisión
  aplazada al issue de implementación.
- La lógica LPACAP de 2 intentos queda habilitada por `numero_intento`, pero la
  regla concreta del motor es trabajo futuro independiente.
